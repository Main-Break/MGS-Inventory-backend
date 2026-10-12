"""
Classe mãe para manipulação do banco de dados, seja ele SQLite ou MySQL.
Esta classe fornece métodos para conectar, desconectar e executar comandos SQL no banco de dados.

Toda função da Database retorna dois parametros, sendo o primeiro um booleano indicando
sucesso ou falha da operação, e o segundo o resultado da operação, que pode ser um dicionário,
uma lista de dicionários ou None, dependendo do tipo de operação realizada.

Regra para escrever SQL no projeto:
    - Sempre use "?" no lugar dos valores, independente do banco.
      O cmd() troca "?" por "%s" sozinho quando o banco for MySQL.
    - Nunca coloque valores direto no texto do SQL, sempre passe em params.

"""

# Imports
import sqlite3
from pathlib import Path
import mysql.connector

#
class Database:

    def __init__(
            self,
            _type: str = "sqlite",
            sqlite_file: str = "database.db",
            mysql_host: str = None,
            mysql_user: str = None,
            mysql_password: str = None,
            mysql_database: str = None
        ) -> None:

        self._type = _type
        self._file = sqlite_file
        self._conn: sqlite3.Connection | mysql.connector.Connection | None = None

        self._DB_HOST = mysql_host
        self._DB_USER = mysql_user
        self._DB_PASSWORD = mysql_password
        self._DB_NAME = mysql_database
    
        # Procura criar o diretório do arquivo de banco de dados, caso não exista.
        Path(self._file).parent.mkdir(parents=True, exist_ok=True)

        # Conecta ao banco de dados dependendo do tipo especificado (SQLite ou MySQL).
        self.connect()

    def connect(self) -> None:
        try:
            if self._type == "sqlite":
                self._conn = sqlite3.connect(self._file)
                self._conn.row_factory = sqlite3.Row
            else:
                self._conn = mysql.connector.connect(
                    host=self._DB_HOST,
                    user=self._DB_USER,
                    password=self._DB_PASSWORD,
                    database=self._DB_NAME
                )

        except sqlite3.Error as e:
            print(f"Erro ao conectar ao banco de dados SQLite: {e}")
            raise

        except mysql.connector.Error as e:
            print(f"Erro ao conectar ao banco de dados MySQL: {e}")
            raise

        except Exception as e:
            print(f"Erro ao conectar ao banco de dados: {e}")
            raise

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None

    def cmd(self, command: str, params: tuple = (), fetch: str = "none") -> bool | None:
        """
        Função geral para envio de comando SQL ao banco de dados, com suporte a parâmetros e diferentes tipos de busca de resultados.
        """

        # Se a conexão não estiver estabelecida, tenta conectar ao banco de dados.
        if self._conn is None:
            self.connect()

        # O SQL do projeto é escrito sempre com "?". O MySQL usa "%s", então troca aqui.
        if self._type != "sqlite":
            command = command.replace("?", "%s")

        # No SQLite o row_factory já devolve linhas que viram dicionário.
        # No MySQL é preciso pedir ao cursor que devolva dicionários.
        if self._type == "sqlite":
            cursor = self._conn.cursor()
        else:
            cursor = self._conn.cursor(dictionary=True)

        # Busca um único resultado da consulta e retorna como um dicionário.
        if fetch == "one":
            cursor.execute(command, params)
            result = cursor.fetchone()
            cursor.close()
            return True, dict(result) if result else None

        # Busca todos os resultados da consulta e retorna uma lista de dicionários.
        elif fetch == "all":
            cursor.execute(command, params)
            results = cursor.fetchall()
            cursor.close()
            return True, [dict(row) for row in results]

        # Caso não seja necessário buscar resultados, apenas executa o comando e confirma a transação.
        # Retorna o id da última linha inserida (útil após um INSERT, nos demais casos pode ser 0 ou None).
        cursor.execute(command, params)
        self._conn.commit()
        last_id = cursor.lastrowid
        cursor.close()
        return True, last_id

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

    def insert_table(self, table: str, columns: list, values: list) -> tuple[bool, int | None]:
        """
        Insere um registro na tabela informada e retorna o id gerado.

        Exemple:
            db.insert_table("users", ["name", "email"], ["User Name", "name@exemple.com"])
        """
        if not columns or len(columns) != len(values):
            raise ValueError("Colunas e valores devem ter a mesma quantidade.")

        # Verifica os nomes antes de montar o SQL.
        self.check_names([table] + columns)

        # Um "?" para cada valor, ex: "?, ?, ?"
        marks = ", ".join(["?"] * len(values))

        command = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({marks})"

        # Os valores vão como parâmetro, nunca no texto do SQL.
        return self.cmd(command, tuple(values))

    def update_table(self, table: str, columns: list, values: list, where_column: str, where_value) -> tuple[bool, None]:
        """
        Atualiza registros da tabela onde where_column for igual a where_value.

        Exemple:
            update_table("users", ["name"], ["Name User."], "user_id", "ID User")
        """
        if not columns or len(columns) != len(values):
            raise ValueError("Colunas e valores devem ter a mesma quantidade.")

        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column] + columns)

        # Monta "coluna1 = ?, coluna2 = ?"
        sets = ", ".join([f"{column} = ?" for column in columns])

        command = f"UPDATE {table} SET {sets} WHERE {where_column} = ?"

        # Os valores vão como parâmetro, nunca no texto do SQL.
        success, _ = self.cmd(command, tuple(values) + (where_value,))
        return success, None

    def delete_data(self, table: str, where_column: str, where_value) -> tuple[bool, None]:
        """
        [ATENÇÃO] Essa função apaga o dado por completo, ela não faz SOFT DELETE.
        Caso queira usar SOFT DELETE, use a função update_table, como no exemplo abaixo:

            update_table("users", ["status"], ["deleted"], "user_id", 1)

        Exemplo:
            db.delete_data("users", "user_id", 1)
            Gera: DELETE FROM users WHERE user_id = ?
        """
        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column])

        command = f"DELETE FROM {table} WHERE {where_column} = ?"

        # O valor vai como parâmetro, nunca no texto do SQL.
        success, _ = self.cmd(command, (where_value,))
        return success, None
