import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 设置页面布局
st.set_page_config(page_title="分包合同数据分析系统", layout="wide")

# 密码验证函数
def check_password():
    """密码验证"""
    def password_entered():
        """检查输入的密码是否正确"""
        if st.session_state["password"] == "yuelifeng@2018":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # 删除密码，不存储
        else:
            st.session_state["password_correct"] = False
    
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if st.session_state["password_correct"]:
        return True
    
    st.title("分包合同数据分析系统")
    st.markdown("---")
    st.subheader("🔒 系统访问认证")
    password = st.text_input(
        "请输入访问密码:", 
        type="password", 
        key="password",
        on_change=password_entered
    )
    
    if "password" in st.session_state and not st.session_state["password_correct"]:
        st.error("密码错误，请重新输入")
    
    st.info("如需访问权限，请联系系统管理员")
    return False

# 检查密码
if not check_password():
    st.stop()

# 主应用
st.title("分包合同数据分析系统")

# 定义文件路径
file_path = "00 分包合同组合表.xlsx"

# 检查文件是否存在
if not os.path.exists(file_path):
    st.error(f"文件未找到: {file_path}")
    st.stop()

# 读取Excel数据
@st.cache_data
def load_data():
    try:
        # 读取组合表数据
        df = pd.read_excel(file_path, sheet_name="组合表")
        
        # 找到A列中首次出现"#VALUE!"的行，截取有效数据
        invalid_row = df[df.iloc[:, 0].astype(str).str.contains("#VALUE!")].index.min()
        if pd.notna(invalid_row):
            df = df.iloc[:invalid_row]
        
        # 处理日期和金额字段
        date_cols = ['签订时间', '履行期限(起)', '履行期限(止)']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        if '标的金额' in df.columns:
            df['标的金额'] = pd.to_numeric(df['标的金额'], errors='coerce')
        
        if '承办部门' in df.columns:
            # 移除部门为空的记录，不填充为"未知部门"
            df = df[df['承办部门'].notna()]
        
        if '超付金额' in df.columns:
            df['超付金额'] = pd.to_numeric(df['超付金额'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"读取数据时出错: {str(e)}")
        return None

df = load_data()
if df is None:
    st.stop()

current_time = datetime.now()

# 设置颜色主题
COLOR_THEME = ['#4E79A7', '#F28E2B', '#E15759', '#76B7B2']

# 创建Plotly 2D图表函数
def create_plotly_2d_chart(data, title, xlabel, ylabel, color_idx=0):
    """使用Plotly创建2D图表"""
    
    if hasattr(data, 'values'):
        values = data.values
        labels = data.index.tolist()
    else:
        values = data
        labels = [f"类别{i}" for i in range(len(data))]
    
    # 创建Plotly柱状图
    fig = go.Figure(data=[
        go.Bar(
            x=labels,
            y=values,
            marker_color=COLOR_THEME[color_idx % len(COLOR_THEME)],
            text=values,
            texttemplate='%{text:.0f}' if '数量' in ylabel else '%{text:,.0f}',
            textposition='outside',
            hovertemplate=(
                f"{xlabel}: %{{x}}<br>{ylabel}: %{{y:,.0f}}<extra></extra>" 
                if '金额' in ylabel else 
                f"{xlabel}: %{{x}}<br>{ylabel}: %{{y}}<extra></extra>"
            )
        )
    ])
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='black')
        ),
        xaxis=dict(
            title=xlabel,
            title_font=dict(size=14, color='gray'),
            tickfont=dict(size=12, color='gray')
        ),
        yaxis=dict(
            title=ylabel,
            title_font=dict(size=14, color='gray'),
            tickfont=dict(size=12, color='gray')
        ),
        showlegend=False,
        height=500,
        margin=dict(l=50, r=50, t=80, b=120),
        plot_bgcolor='white'
    )
    
    return fig

# 设置Plotly中文字体
def setup_plotly_chinese_font(fig):
    """设置Plotly图表的中文字体"""
    fig.update_layout(
        font=dict(
            family="Microsoft YaHei, SimHei, Arial, sans-serif",
            size=12,
        )
    )
    return fig

# 侧边栏布局
with st.sidebar:
    st.header("筛选条件")
    
    # 新增"同时显示"复选框
    show_all = st.checkbox("同时显示", value=False, 
                          help="选中可同时显示所有筛选条件的图表，不选中则只显示当前执行的筛选条件结果")
    
    # 第一部分：合同数量金额
    with st.expander("合同数量金额", expanded=True):
        # 时间范围
        min_date = df['签订时间'].min().to_pydatetime()
        max_date = df['签订时间'].max().to_pydatetime()
        date_col1, date_col2 = st.columns(2)
        with date_col1:
            start_date = st.date_input("最早签订时间", min_date, min_value=min_date, max_value=max_date, key="date1_start")
        with date_col2:
            end_date = st.date_input("最晚签订时间", max_date, min_value=min_date, max_value=max_date, key="date1_end")
        
        # 部门筛选
        departments = df['承办部门'].unique().tolist()
        selected_departments = st.multiselect("选择承办部门", departments, default=departments, key="dept1")
        
        # 采购类别(动态更新)
        if selected_departments:
            procurement_types = df[df['承办部门'].isin(selected_departments)]['选商方式'].unique().tolist()
        else:
            procurement_types = df['选商方式'].unique().tolist()
        selected_types = st.multiselect("选择采购类别", procurement_types, default=procurement_types, key="type1")
        
        apply_filter1 = st.button("执行筛选条件", key="apply1")
    
    # 第二部分：在建项目分析
    with st.expander("在建项目分析", expanded=False):
        # 时间范围
        date_col3, date_col4 = st.columns(2)
        with date_col3:
            start_date2 = st.date_input("最早签订时间", min_date, min_value=min_date, max_value=max_date, key="date2_start")
        with date_col4:
            end_date2 = st.date_input("最晚签订时间", max_date, min_value=min_date, max_value=max_date, key="date2_end")
        
        # 部门筛选
        selected_departments2 = st.multiselect("选择承办部门", departments, default=["经营管理部（预结算中心）"], key="dept2")
        
        apply_filter2 = st.button("执行筛选条件", key="apply2")
    
    # 第三部分：已审定分包付款
    with st.expander("已审定分包付款", expanded=False):
        # 时间范围
        date_col5, date_col6 = st.columns(2)
        with date_col5:
            start_date3 = st.date_input("最早签订时间", min_date, min_value=min_date, max_value=max_date, key="date3_start")
        with date_col6:
            end_date3 = st.date_input("最晚签订时间", max_date, min_value=min_date, max_value=max_date,key="date3_end")
        
        # 部门筛选
        selected_departments3 = st.multiselect("选择承办部门", departments, default=["经营管理部（预结算中心）"], key="dept3")
        
        apply_filter3 = st.button("执行筛选条件", key="apply3")

# 主页面布局
if apply_filter1 or apply_filter2 or apply_filter3 or show_all:
    # 第一部分：合同数量金额
    if show_all or apply_filter1:
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)
        
        filtered_df = df[
            (df['签订时间'] >= start_date) & 
            (df['签订时间'] <= end_date) & 
            (df['选商方式'].isin(selected_types)) &
            (df['承办部门'].isin(selected_departments))
        ].copy()
        
        with st.container():
            st.subheader("合同数量金额分析")
            st.write(f"筛选到 {len(filtered_df)} 条记录")
            
            # 合同数量金额分析
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("合同数量")
                if not filtered_df.empty:
                    counts = filtered_df['选商方式'].value_counts()
                    fig = create_plotly_2d_chart(
                        counts, 
                        "采购类别合同数量分布", 
                        "采购类别", 
                        "合同数量", 
                        0
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("没有符合条件的数据")
                    
            with col2:
                st.subheader("合同金额")
                if not filtered_df.empty:
                    amount_by_type = filtered_df.groupby('选商方式')['标的金额'].sum().sort_values(ascending=False)
                    fig = create_plotly_2d_chart(
                        amount_by_type,
                        "采购类别合同金额分布",
                        "采购类别", 
                        "合同金额 (元)", 
                        1
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("没有符合条件的数据")
    
    # 第二部分：在建项目分析
    if show_all or apply_filter2:
        start_date2 = pd.to_datetime(start_date2)
        end_date2 = pd.to_datetime(end_date2)
        
        # 筛选在建项目（履行期限(止) > 当前时间）
        ongoing_projects = df[
            (df['履行期限(止)'] > current_time) &
            (df['签订时间'] >= start_date2) & 
            (df['签订时间'] <= end_date2) &
            (df['承办部门'].isin(selected_departments2))
        ].copy()
        
        with st.container():
            st.subheader("在建项目分析")
            if not ongoing_projects.empty:
                # 提取年份
                ongoing_projects['年份'] = ongoing_projects['履行期限(起)'].dt.year
                
                # 按年份分组统计
                yearly_stats = ongoing_projects.groupby('年份').agg(
                    项目数量=('标的金额', 'count'),
                    合同金额=('标的金额', 'sum')
                ).reset_index()
                
                col3, col4 = st.columns(2)
                
                with col3:
                    st.subheader("在建项目数量")
                    fig = create_plotly_2d_chart(
                        yearly_stats.set_index('年份')['项目数量'],
                        "在建项目数量按年份分布",
                        "年份", 
                        "项目数量", 
                        2
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                with col4:
                    st.subheader("在建项目金额")
                    fig = create_plotly_2d_chart(
                        yearly_stats.set_index('年份')['合同金额'],
                        "在建项目金额按年份分布", 
                        "年份", 
                        "合同金额 (元)",
                        3
                    )
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("没有符合条件的在建项目")
    
    # 第三部分：已审定分包付款
    if show_all or apply_filter3:
        start_date3 = pd.to_datetime(start_date3)
        end_date3 = pd.to_datetime(end_date3)
        
        payment_df = df[
            (df['签订时间'] >= start_date3) & 
            (df['签订时间'] <= end_date3) &
            (df['承办部门'].isin(selected_departments3))
        ].copy()
        
        with st.container():
            st.subheader("已审定分包付款分析")
            if not payment_df.empty:
                # 提取年份
                payment_df['年份'] = payment_df['签订时间'].dt.year
                
                # 分类超付和未付
                overpaid = payment_df[payment_df['超付金额'] > 0]
                underpaid = payment_df[payment_df['超付金额'] < 0]
                
                # 按年份分组统计
                overpaid_stats = overpaid.groupby('年份').agg(
                    超付数量=('标的金额', 'count'),
                    超付金额=('标的金额', 'sum')
                ).reset_index()
                
                underpaid_stats = underpaid.groupby('年份').agg(
                    未付数量=('标的金额', 'count'),
                    未付金额=('标的金额', 'sum')
                ).reset_index()
                
                col5, col6 = st.columns(2)
                
                with col5:
                    st.subheader("超付情况")
                    if not overpaid.empty:
                        fig = create_plotly_2d_chart(
                            overpaid_stats.set_index('年份')['超付数量'],
                            "超付数量按年份分布",
                            "年份", 
                            "超付数量", 
                            0
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        fig = create_plotly_2d_chart(
                            overpaid_stats.set_index('年份')['超付金额'],
                            "超付金额按年份分布",
                            "年份", 
                            "超付金额 (元)", 
                            1
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("没有超付记录")
                
                with col6:
                    st.subheader("未付情况")
                    if not underpaid.empty:
                        fig = create_plotly_2d_chart(
                            underpaid_stats.set_index('年份')['未付数量'],
                            "未付数量按年份分布",
                            "年份", 
                            "未付数量", 
                            2
                        )
                        st.plotly_chart(fig, use_container_width=True)
                        
                        fig = create_plotly_2d_chart(
                            underpaid_stats.set_index('年份')['未付金额'],
                            "未付金额按年份分布",
                            "年份", 
                            "未付金额 (元)", 
                            3
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning("没有未付记录")
            else:
                st.warning("没有符合条件的付款记录")
else:
    st.info("请在左侧边栏设置筛选条件，然后点击相应的'执行筛选条件'按钮")

# 显示原始数据统计信息
with st.expander("原始数据统计信息"):
    st.subheader("数据概览")
    st.write(f"总记录数: {len(df)}")
    
    st.subheader("各字段统计")
    st.write(df.describe(include='all'))
    
    st.subheader("前5条记录")
    st.dataframe(df.head())
