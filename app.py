import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import calendar
from datetime import datetime, date
import io
import os
import holidays
import urllib.request

# --- 폰트 자동 다운로드 로직 ---
def get_font(font_option, uploaded_font, size, lang, force_bold=False):
    if uploaded_font is not None:
        try:
            return ImageFont.truetype(io.BytesIO(uploaded_font.getvalue()), size)
        except: pass
    font_urls = {
        "나눔고딕": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
        "나눔고딕_Bold": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
        "바탕체": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Regular.ttf",
        "바탕체_Bold": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf"
    }
    target_key = font_option
    if font_option in ["Arial", "맑은 고딕", "나눔고딕"]:
        target_key = "나눔고딕_Bold" if force_bold else "나눔고딕"
    elif font_option == "바탕체":
        target_key = "바탕체_Bold" if force_bold else "바탕체"
    file_name = f"{target_key}.ttf"
    if not os.path.exists(file_name):
        try:
            url = font_urls.get(target_key, font_urls["나눔고딕"])
            urllib.request.urlretrieve(url, file_name)
        except: return ImageFont.load_default()
    return ImageFont.truetype(file_name, size)

def get_calendar_data(year, month, lang, use_holidays):
    cal = calendar.TextCalendar(calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)
    kr_h = holidays.KR(years=year) if use_holidays else {}
    if lang == "한국어":
        m_n, hds = f"{month}월", ["일", "월", "화", "수", "목", "금", "토"]
    else:
        m_n, hds = calendar.month_name[month].upper(), ["S", "M", "T", "W", "T", "F", "S"]
    return m_n, hds, weeks, kr_h

def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image, bg_rotate, bg_x, bg_y, text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold, use_holidays, show_box, box_color_hex, box_opacity, box_radius, show_watermark):
    if bg_type == "이미지 업로드" and bg_image is not None:
        img = Image.open(bg_image).convert("RGBA")
        img = img.rotate(bg_rotate, expand=True)
        w_r, h_r = width / img.width, height / img.height
        n_w, n_h = int(img.width * max(w_r, h_r)), int(img.height * max(w_r, h_r))
        img = img.resize((n_w, n_h), resample=Image.LANCZOS)
        off_x, off_y = int((bg_x / 100) * (n_w - width)), int((bg_y / 100) * (n_h - height))
        left, top = int((n_w - width)/2) + off_x, int((n_h - height)/2) + off_y
        img = img.crop((left, top, left + width, top + height))
    else:
        img = Image.new('RGBA', (width, height), color=bg_color)
    
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    m_n, hds, wks, kr_h = get_calendar_data(year, month, lang, use_holidays)
    b_f = get_font(font_family, uploaded_font, int(font_size * 1.5), lang, True)
    r_f = get_font(font_family, uploaded_font, font_size, lang, is_bold)
    t_c, r_c = ImageColor.getrgb(text_color_hex), (220, 20, 60, 255)
    c_w, r_h = font_size * x_spacing, font_size * y_spacing
    cal_w, cal_h = c_w * 7, r_h * (len(wks) + 2.5)
    s_x, s_y = (width - cal_w) / 2, (height * (pos_ratio / 100)) - (cal_h / 2)
    
    if show_box:
        bc = ImageColor.getrgb(box_color_hex)
        draw.rounded_rectangle([s_x - 40, s_y - 40, s_x + cal_w + 40, s_y + cal_h + 40], radius=box_radius, fill=(bc[0], bc[1], bc[2], int(255 * (box_opacity/100))))
    draw.text((width/2, s_y + r_h/2), m_n, fill=t_c, font=b_f, anchor="mm")
    h_y = s_y + (r_h * 2)
    for i, h in enumerate(hds):
        draw.text((s_x + (i * c_w) + (c_w/2), h_y), h, fill=r_c if i == 0 else t_c, font=r_f, anchor="mm")
    for ri, wk in enumerate(wks):
        y = h_y + (r_h * (ri + 1))
        for ci, dy in enumerate(wk):
            if dy != 0:
                is_h = date(year, month, dy) in kr_h
                draw.text((s_x + (ci * c_w) + (c_w/2), y), str(dy), fill=r_c if (ci == 0 or is_h) else t_c, font=r_f, anchor="mm")
    if show_watermark:
        w_f = get_font(font_family, uploaded_font, 20, lang, True)
        draw.text((width - 30, height - 30), "Moon1", fill=t_c, font=w_f, anchor="rd")
    return Image.alpha_composite(img, overlay).convert("RGB")

# --- UI 레이아웃 ---
st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")
st.markdown("<h2 style='margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("---")
    st.header("1️⃣ 기기 규격 설정")
    category_list = ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"]
    category = st.selectbox("기기 분류", category_list, index=2)
    res_map = {"스마트폰 (1080x2340)": (1080, 2340), "태블릿 (2048x2732)": (2048, 2732), "이북 리더기 (758x1024)": (758, 1024)}
    w, h = (st.number_input("가로", value=1080), st.number_input("세로", value=1920)) if category == "직접 입력" else res_map[category]
    
    st.markdown("---")
    st.header("2️⃣ 날짜 및 위치")
    c1, c2 = st.columns(2)
    year, month = c1.number_input("년", value=2026), c2.number_input("월", 1, 12, 3)
    is_landscape = st.checkbox("🔄 가로로 돌리기", value=False)
    if is_landscape: w, h = h, w
    use_holidays, pos_val = st.checkbox("대한민국 공휴일 반영", value=True), st.slider("세로 위치 (%)", 0, 100, 50)
    
    st.markdown("---")
    st.header("3️⃣ 달력 디자인")
    lang = st.radio("언어", ["English", "한국어"], horizontal=True)
    font_f = st.selectbox("서체", ["Arial", "맑은 고딕", "바탕체", "나눔고딕"], index=0)
    is_bold, t_color = st.checkbox("볼드체 설정", value=False), st.color_picker("텍스트 색상", "#000000")
    up_font = st.file_uploader("외부 폰트 추가", type=['ttf', 'otf'])
    f_size = st.slider("글자 크기", 10, 120, 40)
    x_s, y_s = st.slider("가로 간격", 1.0, 5.0, 2.5), st.slider("세로 간격", 1.0, 5.0, 2.0)
    
    st.markdown("---")
    st.header("4️⃣ 배경 설정")
    bg_type = st.radio("배경 종류", ["단색 컬러", "이미지 업로드"], horizontal=True)
    bg_rotate, bg_x, bg_y, bg_img, bg_color = 0, 0, 0, None, "#FFFFFF"
    
    if bg_type == "이미지 업로드":
        # 💡 슬라이더를 업로드 버튼보다 위로 배치하여 가시성 확보
        st.write("🖼️ **이미지 조작 (회전 및 위치)**")
        bg_rotate = st.slider("이미지 회전 (도)", 0, 360, 0, 90)
        bg_x = st.slider("이미지 가로 이동 (%)", -100, 100, 0)
        bg_y = st.slider("이미지 세로 이동 (%)", -100, 100, 0)
        bg_img = st.file_uploader("이미지 파일 선택", type=['jpg', 'png', 'jpeg'])
    else:
        bg_color = st.color_picker("배경색 선택", "#FFFFFF")
    
    st.markdown("---")
    st.write("🕶️ **박스 설정**")
    show_box = st.checkbox("가독성 박스 추가(이미지 배경 시)", value=False)
    bx_c, bx_o, bx_r = st.color_picker("바탕 색상", "#FFFFFF"), st.slider("바탕 투명도", 0, 100, 100), st.slider("바탕 모서리 곡률", 0, 100, 20)
    
    st.markdown("---")
    st.header("5️⃣ 제작자 출처 표기")
    show_wm = st.checkbox("Moon1 마크 표시", value=False)
    
    # 💡 최종 버전 정보 표기
    st.markdown("---")
    st.caption("🚀 최종 개발자 수정시각: 2026.03.15.03.25")

# 결과 생성
final_img = generate_wallpaper(w, h, year, month, pos_val, bg_type, bg_color, bg_img, bg_rotate, bg_x, bg_y, t_color, f_size, x_s, y_s, lang, font_f, up_font, is_bold, use_holidays, show_box, bx_c, bx_o, bx_r, show_wm)
st.markdown("### 미리보기")
st.image(final_img, width=400)
buf = io.BytesIO()
final_img.save(buf, format="PNG")
st.download_button("📥 이미지 파일로 저장", buf.getvalue(), f"calendar_{year}_{month}.png")
