import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import os

# 设置页面布局
st.set_page_config(page_title="分包合同组合分析系统", layout="wide")

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

# 颜色方案
COLOR_SCHEME = ['#4285F4', '#34A853', '#FBBC05', '#EA4335']

# 创建Plotly图表
def create_plotly_chart(data, title, x_label, y_labels):
    """创建Plotly图表"""
    fig = go.Figure()
    
    for i, y_label in enumerate(y_labels):
        fig.add_trace(go.Bar(
            x=data.index,
            y=data[y_label],
            name=y_label,
            marker_color=COLOR_SCHEME[i % len(COLOR_SCHEME)],
            text=data[y_label],
            texttemplate='%{text:,.0f}' if '金额' in y_label else '%{text}',
            textposition='outside',
            hovertemplate=f"{x_label}: %{{x}}<br>{y_label}: %{{y:,.0f if '金额' in y_label else :.0f}}<extra></extra>"
        ))
    
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor='center',
            font=dict(size=18, color='black')
        ),
        xaxis=dict(
            title=x_label,
            title_font=dict(size=14, color='gray'),
            tickfont=dict(size=12, color='gray')
        ),
        yaxis=dict(
            title_font=dict(size=14, color='gray'),
            tickfont=dict(size=12,color='gray')
        ),
        barmode='group',
        height=500,
        margin=dict(l=50, r=50, t=80, b=120),
        plot_bgcolor='white',
        font=dict(family="Microsoft YaHei, SimHei, Arial, sans-serif")
    )
    
    return fig

# 侧边栏设置
with st.sidebar:
    st.markdown("""
    <style>
    .sidebar .sidebar-content {
        width: 350px;
    }
    .filter-section {
        font-size: 0.8em;
        margin-bottom: 1em;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.header("筛选条件")
    
    # 第一部分筛选条件 - 合同数量金额分析
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("合同数量金额分析")
        
        # 时间范围
        min_date = df['签订时间'].min().to_pydatetime()
        max_date = df['签订时间'].max().to_pydatetime()
        start_date1 = st.date_input("最早签订时间", min_date, min_value=min_date, max_value=max_date, key="start1")
        end_date1 = st.date_input("最晚签订时间", max_date, min_value=min_date, max_value=max_date, key="end1")
        
        # 部门筛选
        departments = df['承办部门'].unique().tolist()
        selected_departments1 = st.multiselect("选择承办部门", departments, default=departments, key="dept1")
        
        # 采购类别(动态更新)
        if selected_departments1:
            procurement_types = df[df['承办部门'].isin(selected_departments1)]['选商方式'].unique().tolist()
        else:
            procurement_types = df['选商方式'].unique().tolist()
        selected_types1 = st.multiselect("选择采购类别", procurement_types, default=procurement_types, key="type1")
        
        apply_filter1 = st.button("执行筛选条件", key="apply1")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 第二部分筛选条件 - 在建项目分析
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("在建项目分析")
        
        start_date2 = st.date_input("最早签订时间", min_date, min_value=min_date, max_value=max_date, key="start2")
        end_date2 = st.date_input("最晚签订时间", max_date, min_value=min_date, max_value=max_date, key="end2")
        
        selected_departments2 = st.multiselect("选择承办部门", departments, default=["经营管理部（预结算中心）"], key="dept2")
        
        apply_filter2 = st.button("执行筛选条件", key="apply2")
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # 第三部分筛选条件 - 分包付款分析
    with st.container():
        st.markdown('<div class="filter-section">', unsafe_allow_html=True)
        st.subheader("分包付款分析")
        
        start_date3 = st.date_input("最早签订时间", min_date, min_value=min_date, max_value=max_date, key="start3")
        end_date3 = st.date_input("最晚签订时间", max_date, min_value=min_date, max_value=max_date, key="end3")
        
        selected_departments3 = st.multiselect("选择承办部门", departments, default=["经营管理部（预结算中心）"], key="dept3")
        
        apply_filter3 = st.button("执行筛选条件", key="apply3")
        st.markdown('</div>', unsafe_allow_html=True)

# 主页面布局 - 调整比例为左侧20%，右侧80%
col1, col2 = st.columns([2, 8])

# 第一部分结果展示
if apply_filter1:
    with col2:
        filtered_df1 = df[
            (df['签订时间'] >= pd.to_datetime(start_date1)) & 
            (df['签订时间'] <= pd.to_datetime(end_date1)) & 
            (df['承办部门'].isin(selected_departments1)) &
            (df['选商方式'].isin(selected_types1))
        ].copy()
        
        if not filtered_df1.empty:
            # 按采购类别分组统计
            stats1 = filtered_df1.groupby('选商方式').agg(
                合同数量=('标的金额', 'count'),
                合同金额=('标的金额', 'sum')
            ).reset_index().set_index('选商方式')
            
            st.subheader("合同数量金额分析结果")
            fig1 = create_plotly_chart(
                stats1,
                "采购类别合同数量与金额分析",
                "采购类别",
                ["合同数量", "合同金额"]
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("没有符合条件的数据")

# 第二部分结果展示
if apply_filter2:
    with col2:
        # 筛选在建项目（履行期限(止) > 当前时间）
        ongoing_projects = df[
            (df['签订时间'] >= pd.to_datetime(start_date2)) & 
            (df['签订时间'] <= pd.to_datetime(end_date2)) & 
            (df['履行期限(止)'] > current_time) &
            (df['承办部门'].isin(selected_departments2))
        ].copy()
        
        if not ongoing_projects.empty:
            # 提取年份
            ongoing_projects['年份'] = ongoing_projects['履行期限(起)'].dt.year
            
            # 按年份分组统计
            stats2 = ongoing_projects.groupby('年份').agg(
                在建项目数量=('标的金额', 'count'),
                在建项目金额=('标的金额', 'sum')
            ).reset_index().set_index('年份')
            
            st.subheader("在建项目分析结果")
            fig2 = create_plotly_chart(
                stats2,
                "在建项目数量与金额分析",
                "年份",
                ["在建项目数量", "在建项目金额"]
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("没有符合条件的在建项目")

# 第三部分结果展示
if apply_filter3:
    with col2:
        filtered_df3 = df[
            (df['签订时间'] >= pd.to_datetime(start_date3)) & 
            (df['签订时间'] <= pd.to_datetime(end_date3)) & 
            (df['承办部门'].isin(selected_departments3))
        ].copy()
        
        if not filtered_df3.empty:
            # 计算超付和未付
            overpaid = filtered_df3[filtered_df3['超付金额'] > 0]
            unpaid = filtered_df3[filtered_df3['超付金额'] < 0]
            
            # 按年份分组统计
            filtered_df3['年份'] = filtered_df3['签订时间'].dt.year
            overpaid_stats = overpaid.groupby('年份').agg(
                已定超付数量=('超付金额', 'count'),
                已定超付金额=('超付金额', 'sum')
            )
            unpaid_stats = unpaid.groupby('年份').agg(
                已定未付数量=('超付金额', 'count'),
                已定未付金额=('超付金额', 'sum')
            )
            
            # 合并结果
            stats3 = pd.concat([overpaid_stats, unpaid_stats], axis=1).fillna(0)
            stats3['已定未付金额'] = stats3['已定未付金额'].abs()  # 取绝对值
            
            st.subheader("分包付款分析结果")
            fig3 = create_plotly_chart(
                stats3,
                "分包付款分析",
                "年份",
                ["已定超付数量", "已定超付金额", "已定未付数量", "已定未付金额"]
            )
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.warning("没有符合条件的数据")

# 初始显示提示
if not (apply_filter1 or apply_filter2 or apply_filter3):
    st.info("请在左侧边栏设置筛选条件，然后点击相应的'执行筛选条件'按钮")
