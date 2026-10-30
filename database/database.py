"""
Classe mãe de acesso ao banco de dados (MySQL / MariaDB).

Regra principal do projeto: comando SQL só existe aqui dentro.
Os models (pasta models/) herdam desta classe e usam apenas as funções abaixo:

    insert_table  -> INSERT
    update_table  -> UPDATE
    delete_data   -> DELETE
    select_one    -> SELECT de um registro
    select_all    -> SELECT de vários registros
    search_data   -> SELECT com busca por texto (LIKE)

Assim, se um dia a forma de falar com o banco mudar, só este arquivo muda.

Toda função retorna dois valores: (sucesso, dado).
    - sucesso: True se o comando rodou, False se deu erro no banco.
    - dado: o resultado (dicionário, lista de dicionários, id gerado ou None).

Proteção contra SQL Injection:
    - Valores sempre vão como parâmetro (%s), nunca escritos no texto do SQL.
    - Nomes de tabela e coluna passam pelo check_names, que só aceita letras, números e "_".
"""

# Imports
import uuid
import mysql.connector


class Database:

    def __init__(self, host: str, port: int, user: str, password: str, database: str) -> None:
        self._host = host
        self._port = port
        self._user = user
        self._password = password
        self._database = database

    def connect(self) -> mysql.connector.MySQLConnection:
        """
        Abre uma conexão nova com o banco.
        Cada comando abre e fecha a sua própria conexão, pois o FastAPI atende
        várias requisições ao mesmo tempo e uma conexão não pode ser dividida entre elas.
        """
        return mysql.connector.connect(
            host=self._host,
            port=self._port,
            user=self._user,
            password=self._password,
            database=self._database
        )

    def cmd(self, command: str, params: tuple = (), fetch: str = "none") -> tuple[bool, dict | list | None]:
        """
        Executa um comando SQL. Uso interno desta classe, os models não devem chamar direto.

        fetch:
            "one"  -> retorna um registro (dicionário) ou None
            "all"  -> retorna uma lista de registros
            "none" -> não retorna nada, apenas executa e confirma (INSERT, UPDATE, DELETE)
        """
        conn = None
        try:
            conn = self.connect()

            # dictionary=True faz cada linha vir como dicionário, ex: {"id": "...", "name": "..."}
            cursor = conn.cursor(dictionary=True)
            cursor.execute(command, params)

            if fetch == "one":
                result = cursor.fetchone()
            elif fetch == "all":
                result = cursor.fetchall()
            else:
                conn.commit()
                result = None

            cursor.close()
            return True, result

        except mysql.connector.Error as error:
            print(f"[BANCO DE DADOS] Erro ao executar comando: {error}")
            return False, None

        finally:
            if conn is not None:
                conn.close()

    def check_names(self, names: list) -> None:
        """
        Verifica se os nomes de tabela e coluna são seguros.
        Nomes não podem ir como parâmetro igual aos valores, então entram no texto do SQL.
        Por isso só aceitamos letras, números e "_" (ex: "users", "created_at").
        Qualquer outro caractere (espaço, aspas, ponto e vírgula...) é recusado.
        """
        for name in names:
            if not name.replace("_", "").isalnum() or not name.isascii():
                raise ValueError(f"Nome de tabela ou coluna inválido: {name}")

    def insert_table(self, table: str, columns: list, values: list) -> tuple[bool, str | None]:
        """
        Insere um registro na tabela informada e retorna o id gerado.
        O id é um UUID-4 gerado aqui, então não precisa ser informado nas colunas.

        Exemplo:
            insert_table("users", ["name", "email"], ["User Name", "name@exemple.com"])
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
        return success, new_id if success else None

    def update_table(self, table: str, columns: list, values: list, where_column: str, where_value) -> tuple[bool, None]:
        """
        Atualiza registros da tabela onde where_column for igual a where_value.

        Exemplo:
            update_table("users", ["name"], ["User Name"], "id", "ID User")
            Gera: UPDATE users SET name = %s WHERE id = %s
        """
        if not columns or len(columns) != len(values):
            raise ValueError("Colunas e valores devem ter a mesma quantidade.")

        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column] + columns)

        # Monta "coluna1 = %s, coluna2 = %s"
        sets = ", ".join([f"{column} = %s" for column in columns])

        command = f"UPDATE {table} SET {sets} WHERE {where_column} = %s"

        # Os valores vão como parâmetro, nunca no texto do SQL.
        return self.cmd(command, tuple(values) + (where_value,))

    def delete_data(self, table: str, where_column: str, where_value) -> tuple[bool, None]:
        """
        [ATENÇÃO] Essa função apaga o dado por completo, ela não faz SOFT DELETE.
        Caso queira usar SOFT DELETE, use a função update_table, como no exemplo abaixo:

            update_table("users", ["status"], ["deleted"], "id", "ID User")

        Exemplo:
            delete_data("users", "id", "ID User")
            Gera: DELETE FROM users WHERE id = %s
        """
        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column])

        command = f"DELETE FROM {table} WHERE {where_column} = %s"

        # O valor vai como parâmetro, nunca no texto do SQL.
        return self.cmd(command, (where_value,))

    def select_one(self, table: str, where_column: str, where_value) -> tuple[bool, dict | None]:
        """
        Busca um registro da tabela onde where_column for igual a where_value.
        Se não encontrar, o dado retornado é None.

        Exemplo:
            select_one("users", "email", "name@exemple.com")
            Gera: SELECT * FROM users WHERE email = %s LIMIT 1
        """
        # Verifica os nomes antes de montar o SQL.
        self.check_names([table, where_column])

        command = f"SELECT * FROM {table} WHERE {where_column} = %s LIMIT 1"

        # O valor vai como parâmetro, nunca no texto do SQL.
        return self.cmd(command, (where_value,), fetch="one")

    def select_all(
            self,
            table: str,
            where_column: str = None,
            where_value=None,
            order_by: str = None,
            descending: bool = False
        ) -> tuple[bool, list]:
        """
        Busca vários registros da tabela. O filtro e a ordenação são opcionais.

        Exemplos:
            select_all("users", order_by="name")
            Gera: SELECT * FROM users ORDER BY name

            select_all("verifications", "user_id", "ID User", order_by="created_at", descending=True)
            Gera: SELECT * FROM verifications WHERE user_id = %s ORDER BY created_at DESC
        """
        # Verifica os nomes antes de montar o SQL.
        self.check_names([table])

        command = f"SELECT * FROM {table}"
        params = ()

        if where_column:
            self.check_names([where_column])
            command += f" WHERE {where_column} = %s"
            params = (where_value,)

        if order_by:
            self.check_names([order_by])
            command += f" ORDER BY {order_by}"
            if descending:
                command += " DESC"

        success, result = self.cmd(command, params, fetch="all")
        return success, result if success else []

    def search_data(self, table: str, columns: list, term: str, order_by: str = None) -> tuple[bool, list]:
        """
        Busca registros em que o texto aparece em qualquer uma das colunas informadas.

        Exemplo:
            search_data("users", ["name", "email"], "kai", order_by="name")
            Gera: SELECT * FROM users WHERE name LIKE %s OR email LIKE %s ORDER BY name
        """
        if not columns:
            raise ValueError("Informe ao menos uma coluna para a busca.")

        # Verifica os nomes antes de montar o SQL.
        self.check_names([table] + columns)

        # Monta "coluna1 LIKE %s OR coluna2 LIKE %s"
        conditions = " OR ".join([f"{column} LIKE %s" for column in columns])
        command = f"SELECT * FROM {table} WHERE {conditions}"

        if order_by:
            self.check_names([order_by])
            command += f" ORDER BY {order_by}"

        # O mesmo termo vai uma vez para cada coluna, sempre como parâmetro.
        params = tuple([f"%{term}%"] * len(columns))

        success, result = self.cmd(command, params, fetch="all")
        return success, result if success else []
