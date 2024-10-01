from typing import Any, Union

import psycopg2

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class GetSchemaTool(BuiltinTool):
    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
    ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        获取数据库中的所有表和列
        """
        # 获取数据库连接参数
        dbname = tool_parameters.get("dbname", "").strip()
        user = tool_parameters.get("user", "").strip()
        password = tool_parameters.get("password", "").strip()
        host = tool_parameters.get("host", "localhost").strip()
        port = tool_parameters.get("port", "5432").strip()

        # 验证参数
        if not dbname or not user or not password:
            return self.create_text_message("缺少必要的数据库连接信息: dbname, user 或 password")

        try:
            # 连接 PostgreSQL 数据库
            connection = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password,
                host=host,
                port=port
            )
            cursor = connection.cursor()

            # 查询数据库中的所有表
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public';
            """)
            tables = cursor.fetchall()

            if not tables:
                return self.create_text_message("没有找到任何表")

            result = "数据库中的表:\n"
            for table in tables:
                result += f"- {table[0]}\n"

                # 查询每个表的列
                cursor.execute(f"""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = '{table[0]}';
                """)
                columns = cursor.fetchall()

                # 列出表的列
                result += "  列:\n"
                for column in columns:
                    result += f"    - {column[0]} ({column[1]})\n"

            return self.create_text_message(result)

        except Exception as error:
            return self.create_text_message(f"无法连接到 PostgreSQL 数据库: {str(error)}")

        finally:
            if connection:
                cursor.close()
                connection.close()
