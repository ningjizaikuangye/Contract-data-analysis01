import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 设置页面布局
st.set_page_config(page_title="分包合同组合分析", layout="wide")

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
    
    st.title("分包合同组合分析系统")
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

# 密码验证通过，显示主应用
st.title("分包合同组合分析系统")

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
        df = pd.read_excel(file_path, sheet_name="组合表")
        date_cols = ['签订时间', '履行期限(起)', '履行期限(止)']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        numeric_cols = ['标的金额', '超付金额']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        if '承办部门' in df.columns:
            df['承办部门'] = df['承办部门'].fillna('未知部门')
        return df
    except Exception as e:
        st.error(f"读取数据时出错: {str(e)}")
        return None

df = load_data()
if df is None:
    st.stop()

current_time = datetime.now()

# 定义颜色方案
COLOR_SCHEME = ['#4285F4', '#34A853', '#FBBC05', '#EA4335']  # Google主题颜色

# 创建Plotly图表函数
def create_bar_chart(data, title, xlabel, ylabel, color_index=0):
    """创建Plotly柱状图"""
    fig = go.Figure()
    
    if hasattr(data, 'values'):
        values = data.values
        labels = data.index.tolist()
    else:
        values = data
        labels = [f"类别{i}" for i in range(len(data))]
    
    fig.add_trace(go.Bar(
        x=labels,
        y=values,
        marker_color=COLOR_SCHEME[color_index % len(COLOR_SCHEME)],
        text=values,
        texttemplate='%{text:.0f}' if '数量' in ylabel else '%{text:,.0f}',
        textposition='outside',
        hovertemplate=f"{xlabel}: %{{x}}<br>{ylabel}: %{{y:,}}<extra></extra>"
    ))
    
    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#333333'}
        },
        xaxis={
            'title': xlabel,
            'title_font': {'size': 14, 'color': '#666666'},
            'tickfont': {'size': 12, 'color': '#666666'}
        },
        yaxis={
            'title': ylabel,
            'title_font': {'size': 14, 'color': '#666666'},
            'tickfont': {'size': 12, 'color': '#666666'}
        },
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        margin={'l': 50, 'r': 50, 't': 80, 'b': 120}
    )
    
    return fig

# 侧边栏设置
with st.sidebar:
    st.header("筛选条件")
    
    # 第一部分筛选条件：合同数量金额分析
    with st.expander("合同数量金额分析", expanded=True):
        min_date = df['签订时间'].min().to_pydatetime()
        max_date = df['签订时间'].max().to_pydatetime()
        part1_start_date = st.date_input("最早签订时间", min_date, 
                                       min_value=min_date, max_value=max_date, 
                                       key="part1_start")
        part1_end_date = st.date_input("最晚签订时间", max_date, 
                                     min_value=min_date, max_value=max_date,
                                     key="part1_end")
        
        departments = df['承办部门'].unique().tolist()
        part1_selected_dept = st.multiselect("选择承办部门", departments, default=departments,
                                           key="part1_dept")
        
        if part1_selected_dept:
            procurement_types = df[df['承办部门'].isin(part1_selected_dept)]['选商方式'].unique().tolist()
        else:
            procurement_types = df['选商方式'].unique().tolist()
        part1_selected_types = st.multiselect("选择采购类别", procurement_types, default=procurement_types,
                                            key="part1_types")
        
        chart_type_part1 = st.radio("选择图表类型", ["数量分析", "金额分析"], key="chart_type_part1")
    
    # 第二部分筛选条件：在建项目分析
    with st.expander("在建项目分析", expanded=True):
        part2_start_date = st.date_input("最早签订时间", min_date, 
                                       min_value=min_date, max_value=max_date,
                                       key="part2_start")
        part2_end_date = st.date_input("最晚签订时间", max_date, 
                                     min_value=min_date, max_value=max_date,
                                     key="part2_end")
        
        part2_selected_dept = st.multiselect("选择承办部门", departments, 
                                           default=["经营管理部（预结算中心）"],
                                           key="part2_dept")
        
        chart_type_part2 = st.radio("选择图表类型", ["数量分析", "金额分析"], key="chart_type_part2")
    
    # 第三部分筛选条件：分包付款分析
    with st.expander("分包付款分析", expanded=True):
        part3_start_date = st.date_input("最早签订时间", min_date, 
                                       min_value=min_date, max_value=max_date,
                                       key="part3_start")
        part3_end_date = st.date_input("最晚签订时间", max_date, 
                                     min_value=min_date, max_value=max_date,
                                     key="part3_end")
        
        part3_selected_dept = st.multiselect("选择承办部门", departments, 
                                           default=["经营管理部（预结算中心）"],
                                           key="part3_dept")
        
        chart_type_part3 = st.radio("选择图表类型", ["超付分析", "未付分析"], key="chart_type_part3")
    
    # 执行筛选按钮
    apply_filter = st.button("执行筛选条件")

# 主页面
if apply_filter:
    # 转换为pandas datetime
    part1_start_date = pd.to_datetime(part1_start_date)
    part1_end_date = pd.to_datetime(part1_end_date)
    part2_start_date = pd.to_datetime(part2_start_date)
    part2_end_date = pd.to_datetime(part2_end_date)
    part3_start_date = pd.to_datetime(part3_start_date)
    part3_end_date = pd.to_datetime(part3_end_date)
    
    # 第一部分筛选结果：合同数量金额分析
    filtered_part1 = df[
        (df['签订时间'] >= part1_start_date) & 
        (df['签订时间'] <= part1_end_date) & 
        (df['承办部门'].isin(part1_selected_dept)) &
        (df['选商方式'].isin(part1_selected_types))
    ].copy()
    
    # 第二部分筛选结果：在建项目分析
    filtered_part2 = df[
        (df['签订时间'] >= part2_start_date) & 
        (df['签订时间'] <= part2_end_date) & 
        (df['承办部门'].isin(part2_selected_dept)) &
        (df['履行期限(止)'] > current_time)
    ].copy()
    
    # 第三部分筛选结果：分包付款分析
    filtered_part3 = df[
        (df['签订时间'] >= part3_start_date) & 
        (df['签订时间'] <= part3_end_date) & 
        (df['承办部门'].isin(part3_selected_dept))
    ].copy()
    
    # 显示筛选结果
    col1, col2 = st.columns(2)
    with col1:
        st.metric("合同数量筛选结果", len(filtered_part1))
    with col2:
        st.metric("在建项目筛选结果", len(filtered_part2))
    
    # 第一部分图表：合同数量金额分析
    st.subheader("合同数量金额分析")
    if not filtered_part1.empty:
        if chart_type_part1 == "数量分析":
            counts = filtered_part1['选商方式'].value_counts()
            fig = create_bar_chart(counts, "采购类别合同数量分布", "采购类别", "合同数量", 0)
            st.plotly_chart(fig, use_container_width=True)
        else:
            amount_by_type = filtered_part1.groupby('选商方式')['标的金额'].sum().sort_values(ascending=False)
            fig = create_bar_chart(amount_by_type, "采购类别合同金额分布", "采购类别", "合同金额 (元)", 1)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("没有符合条件的合同数据")
    
    # 第二部分图表：在建项目分析
    st.subheader("在建项目分析")
    if not filtered_part2.empty:
        filtered_part2['年份'] = filtered_part2['履行期限(起)'].dt.year
        yearly_stats = filtered_part2.groupby('年份').agg(
            项目数量=('标的金额', 'count'),
            合同金额=('标的金额', 'sum')
        ).reset_index()
        
        if chart_type_part2 == "数量分析":
            fig = create_bar_chart(yearly_stats.set_index('年份')['项目数量'], 
                                 "在建项目数量按年份分布", "年份", "项目数量", 2)
            st.plotly_chart(fig, use_container_width=True)
        else:
            fig = create_bar_chart(yearly_stats.set_index('年份')['合同金额'], 
                                 "在建项目金额按年份分布", "年份", "合同金额 (元)", 3)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("没有符合条件的在建项目")
    
    # 第三部分图表：分包付款分析
    st.subheader("分包付款分析")
    if not filtered_part3.empty:
        filtered_part3['年份'] = filtered_part3['签订时间'].dt.year
        
        # 计算超付和未付
        overpaid = filtered_part3[filtered_part3['超付金额'] > 0]
        underpaid = filtered_part3[filtered_part3['超付金额'] < 0]
        
        if chart_type_part3 == "超付分析":
            overpaid_stats = overpaid.groupby('年份').agg(
                超付数量=('超付金额', 'count'),
                超付金额=('超付金额', 'sum')
            ).reset_index()
            
            col1, col2 = st.columns(2)
            with col1:
                fig = create_bar_chart(overpaid_stats.set_index('年份')['超付数量'], 
                                     "已定超付数量按年份分布", "年份", "超付数量", 0)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = create_bar_chart(overpaid_stats.set_index('年份')['超付金额'], 
                                     "已定超付金额按年份分布", "年份", "超付金额 (元)", 1)
                st.plotly_chart(fig, use_container_width=True)
        else:
            underpaid_stats = underpaid.groupby('年份').agg(
                未付数量=('超付金额', 'count'),
                未付金额=('超付金额', 'sum')
            ).reset_index()
            
            col1, col2 = st.columns(2)
            with col1:
                fig = create_bar_chart(underpaid_stats.set_index('年份')['未付数量'], 
                                     "已定未付数量按年份分布", "年份", "未付数量", 2)
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = create_bar_chart(abs(underpaid_stats.set_index('年份')['未付金额']), 
                                     "已定未付金额按年份分布", "年份", "未付金额 (元)", 3)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("没有符合条件的付款数据")
    
    # 添加下载按钮
    st.subheader("数据导出")
    col1, col2, col3 = st.columns(3)
    with col1:
        csv1 = filtered_part1.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下载合同数据 (CSV)",
            data=csv1,
            file_name=f"合同数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
    with col2:
        csv2 = filtered_part2.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下载在建项目数据 (CSV)",
            data=csv2,
            file_name=f"在建项目数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
    with col3:
        csv3 = filtered_part3.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下载付款数据 (CSV)",
            data=csv3,
            file_name=f"付款数据_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
else:
    st.info("请在左侧边栏设置筛选条件，然后点击'执行筛选条件'按钮")

# 显示原始数据统计信息
with st.expander("原始数据统计信息"):
    st.subheader("数据概览")
    st.write(f"总记录数: {len(df)}")
    
    st.subheader("各字段统计")
    st.write(df.describe(include='all'))
    
    st.subheader("前5条记录")
    st.dataframe(df.head())
