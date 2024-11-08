import io
from typing import Any, Union
import psycopg2
import matplotlib.pyplot as plt
from shapely.wkb import loads  # 用于解析 WKB 格式
from shapely.geometry import LineString
import matplotlib.patches as mpatches  # 用于绘制指北针

from core.tools.entities.tool_entities import ToolInvokeMessage
from core.tools.tool.builtin_tool import BuiltinTool


class RoadMapPlotTool(BuiltinTool):
    def _invoke(
        self,
        user_id: str,
        tool_parameters: dict[str, Any],
    ) -> Union[ToolInvokeMessage, list[ToolInvokeMessage]]:
        """
        执行 SQL 查询从 road_202409 表中获取道路信息，并在地图上绘制 geom 列中的道路数据
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

            rows = cursor.fetchall()
            if not rows:
                return self.create_text_message("查询没有返回任何结果")

            # 获取列索引
            column_names = [desc[0] for desc in cursor.description]
            geom_index = column_names.index('geom')  # 找到 geom 列的索引
            tech_class_index = column_names.index('tech_class_name')  # 找到 tech_class_name 列的索引

            # 不同道路等级对应的颜色
            color_map = {
                '高速': 'red',
                '一级': 'green',
                '二级': 'yellow',
                '三级': 'orange',
                '四级': 'blue',
                None: 'gray'  # 对于 null 值
            }

            # 手动排序图例标签
            ordered_labels = ['高速', '一级', '二级', '三级', '四级', None]
            plotted_classes = set()

            # 解析 geom 列并绘制道路
            fig, ax = plt.subplots(figsize=(10, 8))

            # 设置背景为白色
            fig.patch.set_facecolor('white')

            for row in rows:
                geom_wkb = row[geom_index]  # 使用 geom 列的索引来获取 WKB 数据
                tech_class = row[tech_class_index]  # 获取道路技术等级
                color = color_map.get(tech_class, 'gray')  # 获取对应颜色

                line = loads(geom_wkb)  # 使用 Shapely 加载 WKB
                if isinstance(line, LineString):
                    x, y = line.xy
                    # 只为首次出现的道路等级添加标签
                    label = tech_class if tech_class not in plotted_classes else None
                    if label:
                        plotted_classes.add(tech_class)
                    ax.plot(x, y, color=color, label=label)

            ax.set_title("道路地图")

            # 设置黑色边框
            for spine in ax.spines.values():
                spine.set_edgecolor('black')

            # 获取当前图例的 handles 和 labels
            handles, labels = ax.get_legend_handles_labels()

            # 根据 ordered_labels 对 handles 和 labels 重新排序
            sorted_handles_labels = sorted(zip(handles, labels), key=lambda x: ordered_labels.index(x[1]))
            handles, labels = zip(*sorted_handles_labels)

            # 显示排序后的图例，将其移到右侧
            ax.legend(handles, labels, title="道路等级", loc='center left', bbox_to_anchor=(1, 0.5))

            # 移除网格和坐标轴
            ax.grid(False)  # 移除网格
            ax.set_xticks([])  # 移除x轴刻度
            ax.set_yticks([])  # 移除y轴刻度
            ax.set_xlabel('')  # 移除x轴标签
            ax.set_ylabel('')  # 移除y轴标签

            # 将绘制的道路图保存为图片并返回
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches='tight')  # 使用 bbox_inches='tight' 保证布局紧凑
            buf.seek(0)
            plt.close(fig)

            return [
                self.create_text_message("道路图绘制成功，已保存为图片，请您查看"),
                self.create_blob_message(blob=buf.read(), meta={"mime_type": "image/png"}),
            ]

        except Exception as error:
            return self.create_text_message(f"执行 SQL 时发生错误: {str(error)}")

        finally:
            if connection:
                cursor.close()
                connection.close()
