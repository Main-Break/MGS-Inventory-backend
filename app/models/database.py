"""
Classe mãe para manipulação do banco de dados, seja ele SQLite ou MySQL.
Esta classe fornece métodos para conectar, desconectar e executar comandos SQL no banco de dados.

Toda função da Database retorna dois parametros, sendo o primeiro um booleano indicando
sucesso ou falha da operação, e o segundo o resultado da operação, que pode ser um dicionário,
uma lista de dicionários ou None, dependendo do tipo de operação realizada.

"""

# Imports
import sqlite3
from pathlib import Path
import mysql.connector

# 
class Database:    

    def __init__(
            self, 
            type: str = "sqlite", 
            sqlite_file: str = "database.db", 
            mysql_host: str = None,
            mysql_user: str = None,
            mysql_password: str = None,
            mysql_database: str = None
        ) -> None:
        
        self._type = type
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
        return self

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

        # Busca um único resultado da consulta e retorna como um dicionário.
        if fetch == "one":
            cursor = self._conn.cursor()
            cursor.execute(command, params)
            result = cursor.fetchone()
            return True, dict(result) if result else None

        # Busca todos os resultados da consulta e retorna uma lista de dicionários.
        elif fetch == "all":
            cursor = self._conn.cursor()
            cursor.execute(command, params)
            results = cursor.fetchall()
            return True, [dict(row) for row in results]

        # Caso não seja necessário buscar resultados, apenas executa o comando e confirma a transação.
        cursor = self._conn.cursor()
        cursor.execute(command, params)
        self._conn.commit()
        return True, None
