"""
Classe mãe para manipulação do banco de dados MySQL / MariaDB.
Esta classe fornece métodos para conectar, desconectar e executar comandos SQL no banco de dados.

Toda função da Database retorna dois parametros, sendo o primeiro um booleano indicando
sucesso ou falha da operação, e o segundo o resultado da operação, que pode ser um dicionário,
uma lista de dicionários ou None, dependendo do tipo de operação realizada.

Regra para escrever SQL no projeto:
    - Use "%s" no lugar dos valores, ex: "SELECT * FROM users WHERE id = %s".
    - Nunca coloque valores direto no texto do SQL, sempre passe em params.

Os dados de conexão vêm do .env (DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME).

"""

# Imports
import uuid
import mysql.connector
from app.config import Config

#
class Database:

    def __init__(self) -> None:
        config = Config()

        self._DB_HOST = config.DB_HOST
        self._DB_PORT = config.DB_PORT
        self._DB_USER = config.DB_USER
        self._DB_PASSWORD = config.DB_PASSWORD
        self._DB_NAME = config.DB_NAME

        self._conn: mysql.connector.MySQLConnection | None = None

        self.connect()

    def connect(self) -> None:
        try:
            self._conn = mysql.connector.connect(
                host=self._DB_HOST,
                port=self._DB_PORT,
                user=self._DB_USER,
                password=self._DB_PASSWORD,
                database=self._DB_NAME
            )

        except mysql.connector.Error as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def cmd(self, command: str, params: tuple = (), fetch: str = "none") -> tuple[bool, dict | list | None]:
        """
        Função geral para envio de comando SQL ao banco de dados, com suporte a parâmetros e diferentes tipos de busca de resultados.

        Exemplo:
            db.cmd("SELECT * FROM users WHERE id = %s", (user_id,), fetch="one")
        """

        # Se a conexão não estiver estabelecida, tenta conectar ao banco de dados.
        if self._conn is None:
            self.connect()

        # dictionary=True faz cada linha vir como dicionário, ex: {"id": "...", "name": "..."}
        cursor = self._conn.cursor(dictionary=True)

        # Busca um único resultado da consulta.
        if fetch == "one":
            cursor.execute(command, params)
            result = cursor.fetchone()
            cursor.close()
            return True, result

        # Busca todos os resultados da consulta.
        elif fetch == "all":
            cursor.execute(command, params)
            results = cursor.fetchall()
            cursor.close()
            return True, results

        # Caso não seja necessário buscar resultados, apenas executa o comando e confirma a transação.
        cursor.execute(command, params)
        self._conn.commit()
        cursor.close()
        return True, None

    def check_names(self, names: list) -> None:
        """
        Verifica se os nomes de tabela e coluna são seguros.
        Nomes não podem ir como parâmetro igual aos valores, então entram no texto do SQL.
        Por isso só aceitamos letras, números e "_" (ex: "usuarios", "data_criacao").
        Qualquer outro caractere (espaço, aspas, ponto e vírgula...) é recusado.
        """
        for name in names:
            if not name.replace("_", "").isalnum() or not name.isascii():
                raise ValueError(f"Nome de tabela ou coluna inválido: {name}")

    def insert_table(self, table: str, columns: list, values: list) -> tuple[bool, str]:
        """
        Insere um registro na tabela informada e retorna o id gerado.
        O id é um UUID-4 gerado aqui, então não precisa ser informado nas colunas.

        Exemple:
            db.insert_table("users", ["name", "email"], ["User Name", "name@exemple.com"])
            Retorna: (True, "3f1c9a2e-8b4d-4e6f-9a1b-2c3d4e5f6a7b")
        """
        if not columns or len(columns) != len(values):
            raise ValueError("Colunas e valores devem ter a mesma quantidade.")

        # Verifica os nomes antes de montar o SQL.
        self.check_names([table] + columns)

        # Gera o id (UUID-4) e coloca como primeira coluna.
        new_id = str(uuid.uuid4())
        columns = ["id"] + columns
        values = [new_id] + values

        # Um "%s" para cada valor, ex: "%s, %s, %s"
        marks = ", ".join(["%s"] * len(values))

        command = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({marks})"

        # Os valores vão como parâmetro, nunca no texto do SQL.
        success, _ = self.cmd(command, tuple(values))
        return success, new_id

    def update_table(self, table: str, columns: list, values: list, where_column: str, where_value) -> tuple[bool, None]:
        """
        Atualiza registros da tabela onde where_column for igual a where_value.

        Exemple:
            update_table("users", ["name"], ["Name User."], "id", "ID User")
        """
        if not columns or len(columns) != len(values):
            raise ValueError("Colunas e valores devem ter a mesma quantidade.")

        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column] + columns)

        # Monta "coluna1 = %s, coluna2 = %s"
        sets = ", ".join([f"{column} = %s" for column in columns])

        command = f"UPDATE {table} SET {sets} WHERE {where_column} = %s"

        # Os valores vão como parâmetro, nunca no texto do SQL.
        success, _ = self.cmd(command, tuple(values) + (where_value,))
        return success, None

    def delete_data(self, table: str, where_column: str, where_value) -> tuple[bool, None]:
        """
        [ATENÇÃO] Essa função apaga o dado por completo, ela não faz SOFT DELETE.
        Caso queira usar SOFT DELETE, use a função update_table, como no exemplo abaixo:

            update_table("users", ["status"], ["deleted"], "id", "ID User")

        Exemplo:
            db.delete_data("users", "id", "ID User")
            Gera: DELETE FROM users WHERE id = %s
        """
        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column])

        command = f"DELETE FROM {table} WHERE {where_column} = %s"

        # O valor vai como parâmetro, nunca no texto do SQL.
        success, _ = self.cmd(command, (where_value,))
        return success, None
