import subprocess
import pymysql
from pymysql.constants import CLIENT

if __name__ == "__main__":
    with open("docker_cmd.out", "a") as output:
        subprocess.call("docker pull mariadb", shell=True, stdout=output, stderr=output)
        subprocess.call("docker run -p 127.0.0.1:3306:3306  --name some-mariadb -e MARIADB_ROOT_PASSWORD=my-secret-pw -d mariadb:latest", shell=True, stdout=output, stderr=output)

    conn = {
               "host": "127.0.0.1",
               "password": "my-secret-pw",
               "port": 3306,
                "user": "root",
                "client_flag": CLIENT.MULTI_STATEMENTS,
                "database": "sys"
    }

    with open('seedscript.sql','r') as file:
        data = file.read()
    my_query_str = data
    with pymysql.connect(**conn) as cur:
        cur.execute(my_query_str)

    print(my_query_str)
