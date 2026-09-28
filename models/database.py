import sqlite3

"""
Aqui fica a classe principal de banco de dados, a classe Mâe que fornece
as funções básicas para manipulação de banco de dados.


"""


class Database:
    _conn = None
    _file = "database.db"

    def __init__(self, database_file="database.db") -> None:

        self._file = database_file

    def connect(self) -> None:
        # Se já existe conexão, não faz nada
        if self._conn is None:
            self._conn = sqlite3.connect(self.file)
        
        self.cursor = self._conn.cursor()


    def fechar(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None   

    def cmd(self, command, params=(), commit=False, fetch:str="one"):

        try:
            self.connect()

            self.cursor.execute(command, params)
            
            if commit:
                self.conexao.commit()

            if fetch == "all":
                return True, self.cursor.fetchall()

            return True, self.cursor.fetchone()

        except Exception as err:
            return False, str(err)

        finally:
            self.fechar()


    def cmd_multi(self, commands:dict=[], params:dict=[], commit:bool=False, fetch:str=["one"]):
        """
            Executa varios comando 
        """

        result_fetch = []

        try:
            self.connect()


            for idex, command in enumerate(commands):
                
                self.cursor.execute(command, params[idex])

                if commit:
                    self.conexao.commit()

                if fetch == "all":
                    return self.cursor.fetchall()

                return self.cursor.fetchone()

            return result_fetch

        except Exception as err:
            return False, str(err)

        finally:
            self.fechar()


    def update(
            self, 
            table:str, 
            column:str, 
            new_value:str, 
            where:str=None, 
            where_value:str=None, 
            custom_where:str=None
        ) -> bool | str:


        if where and where_value:
            return True, self.cmd(
                command="UPDATE ? SET ? = ? WHERE ? = value",
                params=(table, column, new_value, where),
                commit=True
            )

        if custom_where:
            return True, self.cmd(
                command="UPDATE ? SET ? = ? WHERE ?",
                params=(table, column, new_value, custom_where),
                commit=True
            )

        