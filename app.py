import re
from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Histolab TikTok Shop Dashboard", page_icon="📊", layout="wide")
st.title("Dashboard quản trị TikTok Shop – Histolab Việt Nam")
st.caption("Phân tích dữ liệu vận hành | Giai đoạn nghiên cứu 09/2025–06/2026")

def norm(x): return re.sub(r"\s+"," ",str(x).strip()).lower()
def find_header(raw):
    # File Shop Analytics có phần tổng quan ở đầu; chọn dòng tiêu đề dữ liệu theo ngày.
    for i in range(min(len(raw),30)):
        vals=[norm(v) for v in raw.iloc[i].tolist()]
        if any(v in ["ngày","date","day"] for v in vals) and any(v == "gmv" for v in vals):
            return i
    keys=["gmv","đơn hàng","khách hàng","số món bán ra","hoàn tiền"]
    scores=[]
    for i in range(min(len(raw),30)):
        vals=[norm(v) for v in raw.iloc[i].tolist()]
        scores.append(sum(any(k in v for v in vals) for k in keys))
    return int(np.argmax(scores))
def load_data(file):
    raw=pd.read_excel(file,sheet_name=0,header=None)
    hi=find_header(raw)
    headers=raw.iloc[hi].astype(str).str.strip().tolist()
    d=raw.iloc[hi+1:].copy(); d.columns=headers
    d=d.loc[:,~pd.Index(d.columns).duplicated()].dropna(how="all").reset_index(drop=True)
    dc=next((c for c in d.columns if norm(c) in ["date","day","time"] or "date" in norm(c)),d.columns[0])
    d=d.rename(columns={dc:"Date"})
    # File TikTok Shop đang dùng ngày dd/mm/yyyy; dayfirst=True tránh đảo ngày/tháng.
    d["Date"]=pd.to_datetime(d["Date"],errors="coerce",dayfirst=True)
    d=d[d.Date.notna()].copy()
    for c in d.columns:
        if c!="Date" and d[c].dtype=="object":
            x=d[c].astype(str).str.replace(",","",regex=False).str.replace("%","",regex=False).str.strip()
            n=pd.to_numeric(x,errors="coerce")
            if n.notna().sum(): d[c]=n
    d["Month"]=d.Date.dt.to_period("M").astype(str)
    return d.sort_values("Date").reset_index(drop=True)
def find_col(d,*terms):
    aliases={
      "gmv":["gmv"],"orders":["orders","đơn hàng"],"customers":["customers","khách hàng"],
      "items sold":["items sold","số món bán ra"],"refunds":["refunds","hoàn tiền"],
      "total revenue":["total revenue","tổng doanh thu"],"page views":["page views","lượt xem trang"],
      "visitors":["visitors","khách truy cập"],"conversion rate":["conversion rate","tỷ lệ chuyển đổi"],
      "product impressions":["product impressions","lượt hiển thị sản phẩm"],
      "product clicks":["product clicks","lượt nhấp vào sản phẩm"],"aov":["aov"],
      "linked video gmv":["linked video gmv","gmv đến từ video liên kết"],
      "creator video gmv":["creator video gmv","gmv video của nhà sáng tạo"],
      "creator live gmv":["creator live gmv","gmv live của nhà sáng tạo"]}
    for c in d.columns:
        name=norm(c)
        if all(any(a in name for a in aliases.get(t,[t])) for t in terms): return c
    return None
def fmt_num(v): return "—" if pd.isna(v) else f"{v:,.0f}"
def fmt_money(v): return "—" if pd.isna(v) else f"{v:,.0f} đ"
def fmt_pct(v): return "—" if pd.isna(v) else f"{v:.2f}%"

st.sidebar.header("Nguồn dữ liệu")
uploaded=st.sidebar.file_uploader("Tải file Shop Analytics (.xlsx)",type=["xlsx"])
default=Path("data/Shop Analytics_Key metrics_20260818(1).xlsx")
source=uploaded if uploaded is not None else (default if default.exists() else None)
if source is None:
    st.info("Tải file Shop Analytics Excel ở thanh bên trái để mở dashboard. Không bắt buộc commit dữ liệu doanh nghiệp lên GitHub.")
    st.stop()
try: df=load_data(source)
except Exception as e:
    st.error(f"Không đọc được file Excel: {e}"); st.stop()

cols={
"GMV":find_col(df,"gmv"),"Orders":find_col(df,"orders"),"Customers":find_col(df,"customers"),
"Items sold":find_col(df,"items sold"),"Refunds":find_col(df,"refunds"),
"Total revenue":find_col(df,"total revenue"),"Page views":find_col(df,"page views"),
"Visitors":find_col(df,"visitors"),"Conversion rate":find_col(df,"conversion rate"),
"Product impressions":find_col(df,"product impressions"),"Product clicks":find_col(df,"product clicks"),
"AOV":find_col(df,"aov"),"Linked video GMV":find_col(df,"linked video gmv"),
"Creator video GMV":find_col(df,"creator video gmv"),"Creator LIVE GMV":find_col(df,"creator live gmv")}

# Ép kiểu số cho các cột KPI đã nhận diện. Điều này tránh lỗi mean()/sum()
# khi Excel chứa chuỗi, ô trống hoặc ký hiệu không phải số.
for kpi_col in cols.values():
    if kpi_col is not None:
        df[kpi_col] = pd.to_numeric(
            df[kpi_col].astype(str).str.replace(',', '', regex=False).str.replace('%', '', regex=False).str.strip(),
            errors='coerce'
        )

min_d,max_d=df.Date.min().date(),df.Date.max().date()
st.sidebar.subheader("Bộ lọc thời gian")
dates=st.sidebar.date_input("Khoảng ngày",value=(min_d,max_d),min_value=min_d,max_value=max_d)
start,end=dates if isinstance(dates,(tuple,list)) and len(dates)==2 else (min_d,max_d)
d=df[(df.Date.dt.date>=start)&(df.Date.dt.date<=end)].copy()
if d.empty: st.warning("Không có dữ liệu trong khoảng đã chọn."); st.stop()
d["Month"]=d.Date.dt.to_period("M").astype(str)
agg={}
for k in ["GMV","Orders","Customers","Items sold","Refunds","Total revenue","Page views","Visitors","Product impressions","Product clicks","Linked video GMV","Creator video GMV","Creator LIVE GMV"]:
    if cols[k]: agg[k]=(cols[k],"sum")
m=d.groupby("Month",as_index=False).agg(**agg) if agg else d[["Month"]].drop_duplicates()
for k in ["Conversion rate","AOV"]:
    if cols[k]:
        # Ép kiểu lần nữa sau lọc để chống trường hợp Excel có dữ liệu hỗn hợp.
        d[cols[k]] = pd.to_numeric(d[cols[k]], errors="coerce")
        z=d.groupby("Month")[cols[k]].mean().rename(k+" (daily mean)").reset_index()
        m=m.merge(z,on="Month",how="left")
if "Product impressions" in m and "Product clicks" in m:
    m["CTR (%)"]=np.where(m["Product impressions"]>0,m["Product clicks"]/m["Product impressions"]*100,np.nan)
if "Refunds" in m and "Total revenue" in m:
    m["Refund value / revenue (%)"]=np.where(m["Total revenue"]>0,m["Refunds"]/m["Total revenue"]*100,np.nan)
st.caption(f"Phạm vi: {start:%d/%m/%Y}–{end:%d/%m/%Y} | {len(d):,} dòng ngày hợp lệ")

st.subheader("1. Tổng quan kinh doanh")
kpis=[("GMV","GMV",fmt_money),("Tổng doanh thu","Total revenue",fmt_money),("Đơn hàng","Orders",fmt_num),("Khách hàng","Customers",fmt_num),("Sản phẩm bán ra","Items sold",fmt_num)]
for row_start in range(0,len(kpis),5):
    cc=st.columns(5)
    for i,(label,key,formatter) in enumerate(kpis[row_start:row_start+5]):
        val=pd.to_numeric(d[cols[key]],errors="coerce").sum() if cols[key] else np.nan
        cc[i].metric(label,formatter(val))
if cols["AOV"]: st.caption("AOV trung bình các dòng ngày: "+fmt_money(pd.to_numeric(d[cols["AOV"]],errors="coerce").mean()))
if "GMV" in m: st.plotly_chart(px.line(m,x="Month",y="GMV",markers=True,title="GMV theo tháng"),use_container_width=True)
bars=[k for k in ["Orders","Customers","Items sold"] if k in m]
if bars: st.plotly_chart(px.bar(m.melt(id_vars="Month",value_vars=bars,var_name="Chỉ tiêu",value_name="Giá trị"),x="Month",y="Giá trị",color="Chỉ tiêu",barmode="group",title="Đơn hàng, khách hàng và sản phẩm bán ra"),use_container_width=True)

st.divider(); st.subheader("2. Lưu lượng truy cập và chuyển đổi")
traffic=[("Visitors","Visitors"),("Lượt xem trang","Page views"),("Hiển thị sản phẩm","Product impressions"),("Nhấp sản phẩm","Product clicks")]
cc=st.columns(4)
for i,(label,key) in enumerate(traffic):
    val=pd.to_numeric(d[cols[key]],errors="coerce").sum() if cols[key] else np.nan
    cc[i].metric(label,fmt_num(val))
if cols["Product impressions"] and cols["Product clicks"]:
    imp=pd.to_numeric(d[cols["Product impressions"]],errors="coerce").sum()
    clk=pd.to_numeric(d[cols["Product clicks"]],errors="coerce").sum()
    st.metric("CTR tính từ tổng lượt nhấp / tổng lượt hiển thị",fmt_pct(clk/imp*100 if imp else np.nan))
if cols["Conversion rate"]: st.caption("CVR trung bình theo dòng ngày, theo trường gốc: "+fmt_pct(pd.to_numeric(d[cols["Conversion rate"]],errors="coerce").mean()))
tc=[k for k in ["Visitors","Page views","Product impressions","Product clicks"] if k in m]
if tc: st.plotly_chart(px.line(m,x="Month",y=tc,markers=True,title="Xu hướng traffic và tương tác sản phẩm"),use_container_width=True)
if "Conversion rate (daily mean)" in m: st.plotly_chart(px.line(m,x="Month",y="Conversion rate (daily mean)",markers=True,title="CVR theo tháng (trung bình các dòng ngày)"),use_container_width=True)

st.divider(); st.subheader("3. Nội dung và tiếp thị liên kết")
content=[k for k in ["Linked video GMV","Creator video GMV","Creator LIVE GMV"] if k in m]
if content:
    cc=st.columns(len(content))
    for i,k in enumerate(content):
        cc[i].metric(k,fmt_money(pd.to_numeric(d[cols[k]],errors="coerce").sum()))
    ml=m.melt(id_vars="Month",value_vars=content,var_name="Nguồn/chỉ tiêu",value_name="GMV theo nguồn")
    st.plotly_chart(px.line(ml,x="Month",y="GMV theo nguồn",color="Nguồn/chỉ tiêu",markers=True,title="Các chỉ tiêu GMV theo nguồn nội dung"),use_container_width=True)
st.info("Các trường GMV theo nguồn nội dung có thể khác quy tắc quy thuộc. Không cộng trực tiếp thành tổng Affiliate khi chưa xác minh định nghĩa.")

st.divider(); st.subheader("4. Đơn hàng, hoàn tiền và CSKH")
refund=pd.to_numeric(d[cols["Refunds"]],errors="coerce").sum() if cols["Refunds"] else np.nan
revenue=pd.to_numeric(d[cols["Total revenue"]],errors="coerce").sum() if cols["Total revenue"] else np.nan
cc=st.columns(3); cc[0].metric("Giá trị hoàn tiền",fmt_money(refund)); cc[1].metric("Tổng doanh thu",fmt_money(revenue))
cc[2].metric("Hoàn tiền / doanh thu",fmt_pct(refund/revenue*100 if pd.notna(refund) and pd.notna(revenue) and revenue else np.nan))
if "Refunds" in m: st.plotly_chart(px.bar(m,x="Month",y="Refunds",title="Giá trị hoàn tiền theo tháng"),use_container_width=True)
st.warning("File Shop Analytics tổng hợp chưa đủ để tính tỷ lệ hủy đơn, trả hàng hoặc thời gian CSKH. Cần bổ sung dữ liệu trạng thái đơn và yêu cầu hỗ trợ.")

st.divider(); st.subheader("5. Bảng KPI theo tháng")
st.dataframe(m,use_container_width=True,hide_index=True)
st.download_button("Tải bảng KPI theo tháng (CSV)",data=m.to_csv(index=False).encode("utf-8-sig"),file_name="monthly_kpi.csv",mime="text/csv")

st.divider()
st.subheader("6. KPI mục tiêu dự báo cho giai đoạn tiếp theo")
st.caption("Mốc dữ liệu kết thúc 30/06/2026. KPI mục tiêu = giá trị kỳ cơ sở × 1,10. Đây là mục tiêu kế hoạch, không phải dự báo mô hình thống kê.")
uplift = 0.10
last_date = df["Date"].max().normalize()
june = df[(df["Date"].dt.year == last_date.year) & (df["Date"].dt.month == last_date.month)].copy()
last3_start = (last_date.to_period("M") - 2).start_time
last3 = df[(df["Date"] >= last3_start) & (df["Date"] <= last_date)].copy()

target_metrics = ["GMV", "Orders", "Customers", "Items sold"]
target_cols = {k: cols.get(k) for k in target_metrics}
forecast_rows = []

def safe_sum(data, col):
    return pd.to_numeric(data[col], errors="coerce").sum() if col and not data.empty else np.nan

def safe_daily_avg(data, col):
    if not col or data.empty:
        return np.nan
    daily = data.groupby(data["Date"].dt.date)[col].sum(min_count=1)
    return daily.mean()

# 1) Tuần đầu tháng 7: 01–05/07/2026 (5 ngày), dựa trên trung bình ngày của tháng 06/2026.
week_start = pd.Timestamp("2026-07-01")
week_end = pd.Timestamp("2026-07-05")
for metric in target_metrics:
    col = target_cols[metric]
    daily_base = safe_daily_avg(june, col)
    base = daily_base * (week_end - week_start).days + daily_base if pd.notna(daily_base) else np.nan
    target = base * (1 + uplift) if pd.notna(base) else np.nan
    forecast_rows.append({
        "Tần suất": "Tuần (01–05/07/2026)", "Chỉ tiêu": metric,
        "Kỳ cơ sở": "Bình quân ngày tháng 06/2026 × 5 ngày",
        "Giá trị cơ sở": base, "Tăng mục tiêu (%)": 10,
        "KPI mục tiêu": target, "Công thức": "Bình quân ngày tháng 06 × 5 × 1,10"
    })

# 2) Tháng 07/2026: lấy tháng 06/2026 làm mốc liền trước.
for metric in target_metrics:
    base = safe_sum(june, target_cols[metric])
    forecast_rows.append({
        "Tần suất": "Tháng (07/2026)", "Chỉ tiêu": metric,
        "Kỳ cơ sở": "Thực tế tháng 06/2026",
        "Giá trị cơ sở": base, "Tăng mục tiêu (%)": 10,
        "KPI mục tiêu": base * (1 + uplift) if pd.notna(base) else np.nan,
        "Công thức": "Thực tế tháng 06/2026 × 1,10"
    })

# 3) Quý III/2026: dùng tổng thực tế 3 tháng gần nhất (04–06/2026) làm mốc 3 tháng.
for metric in target_metrics:
    base = safe_sum(last3, target_cols[metric])
    forecast_rows.append({
        "Tần suất": "Quý (Q3/2026: 07–09)", "Chỉ tiêu": metric,
        "Kỳ cơ sở": "Tổng thực tế 3 tháng 04–06/2026",
        "Giá trị cơ sở": base, "Tăng mục tiêu (%)": 10,
        "KPI mục tiêu": base * (1 + uplift) if pd.notna(base) else np.nan,
        "Công thức": "Tổng thực tế 04–06/2026 × 1,10"
    })

forecast_df = pd.DataFrame(forecast_rows)
forecast_df["Đơn vị"] = np.where(forecast_df["Chỉ tiêu"].isin(["GMV"]), "VND", "đơn vị")
st.dataframe(forecast_df, use_container_width=True, hide_index=True)
st.download_button(
    "Tải KPI mục tiêu tuần/tháng/quý (CSV)",
    data=forecast_df.to_csv(index=False).encode("utf-8-sig"),
    file_name="kpi_targets_july_q3_2026_plus_10pct.csv",
    mime="text/csv"
)
plot_df = forecast_df[forecast_df["Chỉ tiêu"] == "GMV"].copy()
if not plot_df.empty:
    st.plotly_chart(
        px.bar(plot_df, x="Tần suất", y="KPI mục tiêu", title="KPI mục tiêu GMV: tuần đầu tháng 7, tháng 7 và quý III/2026"),
        use_container_width=True
    )
st.info("Lưu ý: dữ liệu lịch sử chỉ kết thúc tháng 06/2026. Mục tiêu tuần đầu tháng 7 được tính cho 01–05/07/2026 theo bình quân ngày tháng 6; mục tiêu tháng 7 dựa trên tháng 6; mục tiêu Q3 dựa trên tổng ba tháng 04–06/2026. Đây là cách đặt mục tiêu tăng 10% theo kỳ cơ sở gần nhất, không phải so sánh cùng kỳ năm trước vì chưa có dữ liệu tương ứng.")


with st.expander("Kiểm tra cấu trúc dữ liệu"):
    st.write("Khoảng ngày trong file:",str(df.Date.min().date()),"–",str(df.Date.max().date()))
    st.write("Kiểu dữ liệu KPI đã chuẩn hóa:", {k: str(df[v].dtype) for k,v in cols.items() if v})
    st.write("Các cột được nhận diện:",{k:v for k,v in cols.items() if v})
    st.write("Các KPI chưa tìm thấy:",[k for k,v in cols.items() if not v])
