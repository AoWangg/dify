import psycopg2
from typing import Any, Union

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool

class ExecuteSQLTool(BuiltinTool):
    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
    ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        执行 SQL 并返回结果
        """
        # 获取数据库连接参数
        dbname = tool_parameters.get("dbname", "").strip()
        user = tool_parameters.get("user", "").strip()
        password = tool_parameters.get("password", "").strip()
        host = tool_parameters.get("host", "localhost").strip()
        port = tool_parameters.get("port", "5432").strip()
        sql_query = tool_parameters.get("sql_query", "").strip()

        # 验证参数
        if not dbname or not user or not password:
            return self.create_text_message("缺少必要的数据库连接信息: dbname, user 或 password")
        
        if not sql_query:
            return self.create_text_message("缺少 SQL 查询")

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

            # 执行 SQL 查询
            cursor.execute(sql_query)

            # 如果查询是 SELECT，获取结果
            if sql_query.strip().lower().startswith("select"):
                rows = cursor.fetchall()
                if not rows:
                    return self.create_text_message("查询没有返回任何结果")
                
                # 构建返回结果
                result = "查询结果:\n"
                for row in rows:
                    result += f"{row}\n"
                
            else:
                # 如果不是 SELECT，执行变更操作后获取受影响的行数
                connection.commit()
                result = f"SQL 执行成功, 受影响的行数: {cursor.rowcount}"

            return self.create_text_message(result)

        except Exception as error:
            return self.create_text_message(f"执行 SQL 时发生错误: {str(error)}")

        finally:
            if connection:
                cursor.close()
                connection.close()
