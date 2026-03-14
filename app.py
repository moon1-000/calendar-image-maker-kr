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
    # 1. 사용자가 직접 올린 폰트가 있으면 최우선
    if uploaded_font is not None:
        try:
            return ImageFont.truetype(io.BytesIO(uploaded_font.getvalue()), size)
        except: pass

    # 2. 서체별 다운로드 URL 설정 (구글 공식 폰트 저장소)
    # Arial/맑은고딕 대신 가장 유사하고 안정적인 나눔 시리즈를 사용합니다.
    font_urls = {
        "나눔고딕": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
        "나눔고딕_Bold": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
        "바탕체": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Regular.ttf",
        "바탕체_Bold": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf"
    }

    # 매핑 설정
    target_key = font_option
    if font_option in ["Arial", "맑은 고딕", "나눔고딕"]:
        target_key = "나눔고딕_Bold" if force_bold else "나눔고딕"
    elif font_option == "바탕체":
        target_key = "바탕체_Bold" if force_bold else "바탕체"

    file_name = f"{target_key}.ttf"

    # 3. 폰트 파일이 없으면 인터넷에서 즉시 다운로드
    if not os.path.exists(file_name):
        url = font_urls.get(target_key, font_urls["나눔고딕"])
        try:
            with st.spinner(f'{target_key} 서체를 준비 중입니다...'):
                urllib.request.urlretrieve(url, file_name)
        except:
            return ImageFont.load_default()

    return ImageFont.truetype(file_name, size)

def get_calendar_data(year, month, lang, use_holidays):
    cal = calendar.TextCalendar(calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)
    kr_holidays = holidays.KR(years=year) if use_holidays else {}
    if lang == "한국어":
        m_name, headers = f"{month}월", ["일", "월", "화", "수", "목", "금", "토"]
    else:
        m_name, headers = calendar.month_name[month].upper(), ["S", "M", "T", "W", "T", "F", "S"]
    return m_name, headers, weeks, kr_holidays

def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image, text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold, use_holidays, show_box, box_color_hex, box_opacity, box_radius, show_watermark):
    if bg_type == "이미지 업로드" and bg_image is not None:
        img = Image.open(bg_image).convert("RGBA")
        img = ImageOps.fit(img, (width, height), centering=(0.5, 0.5))
    else:
        img = Image.new('RGBA', (width, height), color=bg_color)
    overlay = Image.new('RGBA', img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    m_name, headers, weeks, kr_holidays = get_calendar_data(year, month, lang, use_holidays)
    bold_font = get_font(font_family, uploaded_font, int(font_size * 1.5), lang, force_bold=True)
    reg_font = get_font(font_family, uploaded_font, font_size, lang, force_bold=is_bold)
    text_color = ImageColor.getrgb(text_color_hex)
    red_color = (220, 20, 60, 255)
    col_width, row_height = font_size * x_spacing, font_size * y_spacing
    cal_width, cal_height = col_width * 7, row_height * (len(weeks) + 2.5)
    start_x, start_y = (width - cal_width) / 2, (height * (pos_ratio / 100)) - (cal_height / 2)
    if show_box:
        b_c = ImageColor.getrgb(box_color_hex)
        draw.rounded_rectangle([start_x - 40, start_y - 40, start_x + cal_width + 40, start_y + cal_height + 40], radius=box_radius, fill=(b_c[0], b_c[1], b_c[2], int(255 * (box_opacity/100))))
    draw.text((width/2, start_y + row_height/2), m_name, fill=text_color, font=bold_font, anchor="mm")
    header_y = start_y + (row_height * 2)
    for i, h in enumerate(headers):
        draw.text((start_x + (i * col_width) + (col_width / 2), header_y), h, fill=red_color if i == 0 else text_color, font=reg_font, anchor="mm")
    for r_idx, week in enumerate(weeks):
        y = header_y + (row_height * (r_idx + 1))
        for c_idx, day in enumerate(week):
            if day != 0:
                is_h = date(year, month, day) in kr_holidays
                draw.text((start_x + (c_idx * col_width) + (col_width / 2), y), str(day), fill=red_color if (c_idx == 0 or is_h) else text_color, font=reg_font, anchor="mm")
    if show_watermark:
        sm_font = get_font(font_family, uploaded_font, 20, lang, force_bold=True)
        draw.text((width - 30, height - 30), "Moon1", fill=text_color, font=sm_font, anchor="rd")
    return Image.alpha_composite(img, overlay).convert("RGB")

st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")
st.markdown("<h2 style='margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("1. 기기 규격 설정")
    cat = st.selectbox("기기 분류", ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"], index=2)
    res = {"스마트폰 (1080x2340)": (1080, 2340), "태블릿 (2048x2732)": (2048, 2732), "이북 리더기 (758x1024)": (758, 1024)}
    w, h = (st.number_input("가로", value=1080), st.number_input("세로", value=1920)) if cat == "직접 입력" else res[cat]
    st.header("2. 날짜 및 위치")
    c1, c2 = st.columns(2)
    year, month = c1.number_input("년", value=2026), c2.number_input("월", 1, 12, 3)
    is_landscape = st.checkbox("🔄 가로로 돌리기", value=False)
    if is_landscape: w, h = h, w
    use_holidays, pos_val = st.checkbox("대한민국 공휴일 반영", value=True), st.slider("세로 위치 (%)", 0, 100, 50)
    st.header("3. 달력 디자인")
    lang = st.radio("언어", ["English", "한국어"], horizontal=True)
    font_family = st.selectbox("서체", ["Arial", "맑은 고딕", "바탕체", "나눔고딕"], index=0)
    is_bold, text_color = st.checkbox("볼드체 설정", value=False), st.color_picker("텍스트 색상", "#000000")
    uploaded_font = st.file_uploader("외부 폰트 추가 (.ttf, .otf)", type=['ttf', 'otf'])
    font_size = st.slider("글자 크기", 10, 120, 35)
    x_s, y_s = st.slider("가로 간격", 1.0, 5.0, 2.5), st.slider("세로 간격", 1.0, 5.0, 2.0)
    st.header("4. 배경 설정")
    bg_type = st.radio("배경", ["단색 컬러", "이미지 업로드"], horizontal=True)
    bg_color = st.color_picker("배경색 선택", "#FFFFFF")
    bg_img = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg']) if bg_type == "이미지 업로드" else None
    st.markdown("---")
    show_box = st.checkbox("가독성 박스 추가(이미지 배경 시)", value=False)
    bx_c, bx_o, bx_r = st.color_picker("바탕 색상", "#FFFFFF"), st.slider("바탕 투명도", 0, 100, 100), st.slider("바탕 모서리 곡률", 0, 100, 20)
    st.header("5. 제작자 출처 표기")
    show_wm = st.checkbox("Moon1 마크 표시", value=False)

final_img = generate_wallpaper(w, h, year, month, pos_val, bg_type, bg_color, bg_img, text_color, font_size, x_s, y_s, lang, font_family, uploaded_font, is_bold, use_holidays, show_box, bx_c, bx_o, bx_r, show_wm)
st.markdown("### 미리보기")
st.image(final_img, width=400)
buf = io.BytesIO()
final_img.save(buf, format="PNG")
st.download_button("📥 이미지 저장", buf.getvalue(), f"calendar_{year}_{month}.png")
