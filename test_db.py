import pymysql

try:
    connection = pymysql.connect(
        host='127.0.0.1',
        user='root',
        password='0633',
        database='toktok',
        port=3306
    )
    print("데이터베이스 연결 성공!")
    connection.close()
except Exception as e:
    print(f"데이터베이스 연결 실패: {e}") 