from backend.database.db import get_connection


def test_database_connection():
    try:
        with get_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        current_database(),
                        current_user,
                        version()
                    """
                )

                result = cursor.fetchone()

                print("Database connection successful!")
                print(f"Database: {result[0]}")
                print(f"User: {result[1]}")
                print(f"PostgreSQL version: {result[2]}")

    except Exception as error:
        print("Database connection failed.")
        print(f"Error type: {type(error).__name__}")
        print(f"Error details: {error}")
        raise


if __name__ == "__main__":
    test_database_connection()