import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageColor
import calendar
from datetime import datetime, date
import io
import os
import holidays
import urllib.request

# --- 폰트 및 데이터 로직 ---
def get_font(font_option, uploaded_font, size, lang, force_bold=False):
    if uploaded_font is not None:
        try: return ImageFont.truetype(io.BytesIO(uploaded_font.getvalue()), size)
        except: pass
    font_urls = {
        "나눔고딕": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
        "나눔고딕_Bold": "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Bold.ttf",
        "바탕체": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Regular.ttf",
        "바탕체_Bold": "https://github.com/google/fonts/raw/main/ofl/nanummyeongjo/NanumMyeongjo-Bold.ttf"
    }
    key = font_option if font_option not in ["Arial", "맑은 고딕"] else "나눔고딕"
    if force_bold: key += "_Bold"
    file_name = f"{key}.ttf"
    if not os.path.exists(file_name):
        try: urllib.request.urlretrieve(font_urls.get(key, font_urls["나눔고딕"]), file_name)
        except: return ImageFont.load_default()
    return ImageFont.truetype(file_name, size)

def get_calendar_data(year, month, lang, use_holidays):
    cal = calendar.TextCalendar(calendar.SUNDAY)
    weeks = cal.monthdayscalendar(year, month)
    kr_h = holidays.KR(years=year) if use_holidays else {}
    m_n = f"{month}월" if lang == "한국어" else calendar.month_name[month].upper()
    hds = ["일", "월", "화", "수", "목", "금", "토"] if lang == "한국어" else ["S", "M", "T", "W", "T", "F", "S"]
    return m_n, hds, weeks, kr_h

# --- 생성 함수 ---
def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image, bg_rotate, bg_x, bg_y, bg_zoom, text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold, use_holidays, show_box, box_color_hex, box_opacity, box_radius, show_moon1, show_custom, custom_text, wm_color):
    base_color = ImageColor.getrgb(bg_color)
    img_canvas = Image.new('RGBA', (width, height), color=base_color)

    if bg_type == "이미지 업로드" and bg_image is not None:
        src_img = Image.open(bg_image).convert("RGBA")
        src_img = src_img.rotate(bg_rotate, expand=True, resample=Image.BICUBIC)
        w_r, h_r = width / src_img.width, height / src_img.height
        base_scale = max(w_r, h_r) * bg_zoom
        n_w, n_h = int(src_img.width * base_scale), int(src_img.height * base_scale)
        src_img = src_img.resize((n_w, n_h), resample=Image.LANCZOS)
        off_x, off_y = int((bg_x / 100) * (n_w - width)), int((bg_y / 100) * (n_h - height))
        left, top = int((n_w - width)/2) + off_x, int((n_h - height)/2) + off_y
        src_img = src_img.crop((left, top, left + width, top + height))
        img_canvas.paste(src_img, (0,0), src_img)
    
    overlay = Image.new('RGBA', (width, height), (0,0,0,0))
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
                
    # 5번 출처 로직 💡
    wm_f = get_font(font_family, uploaded_font, 20, lang, True)
    curr_y = height - 30
    if show_moon1:
        draw.text((width - 30, curr_y), "Moon1", fill=wm_color, font=wm_f, anchor="rd")
        curr_y -= 30
    if show_custom and custom_text:
        draw.text((width - 30, curr_y), custom_text, fill=wm_color, font=wm_f, anchor="rd")
        
    return Image.alpha_composite(img_canvas, overlay).convert("RGB")

# --- UI 레이아웃 ---
st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")
# 제목 10% 축소 💡
st.markdown("<h2 style='font-size: 1.8rem; text-align: center; margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ 설정 메뉴")
    
    st.info("1️⃣ **화면 비율 설정**")
    cat = st.selectbox("기기 분류", ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"], index=2)
    res = {"스마트폰 (1080x2340)": (1080, 2340), "태블릿 (2048x2732)": (2048, 2732), "이북 리더기 (758x1024)": (758, 1024)}
    w, h = (st.number_input("가로", value=1080), st.number_input("세로", value=1920)) if cat == "직접 입력" else res[cat]
    
    st.markdown("---")
    st.info("2️⃣ **달력 시기 및 위치**")
    c1, c2 = st.columns(2)
    year, month = c1.number_input("년", value=2026), c2.number_input("월", 1, 12, 3)
    is_landscape = st.checkbox("가로로 돌리기", value=False)
    if is_landscape: w, h = h, w
    use_holidays, pos_val = st.checkbox("대한민국 공휴일 반영", value=True), st.slider("세로 위치 (%)", 0, 100, 50)
    
    st.markdown("---")
    st.info("3️⃣ **배경 설정**") # 순서 변경 💡 (기존 4번)
    bg_type = st.radio("배경 종류", ["단색 컬러", "이미지 업로드"], horizontal=True)
    bg_rotate, bg_x, bg_y, bg_zoom, bg_img, bg_color = 0, 0, 0, 1.0, None, "#FFFFFF"
    if bg_type == "이미지 업로드":
        bg_img = st.file_uploader("이미지 파일 선택", type=['jpg', 'png', 'jpeg'])
        st.write("🖼️ **이미지 조작**")
        bg_rotate = st.slider("이미지 회전 (도)", 0, 360, 0, 1) # 1도 단위
        bg_zoom = st.slider("이미지 확대 (Zoom)", 1.0, 3.0, 1.0, 0.1)
        bg_x, bg_y = st.slider("이미지 가로 이동 (%)", -100, 100, 0), st.slider("이미지 세로 이동 (%)", -100, 100, 0)
        bg_color = st.color_picker("이미지 외곽 배경색", "#FFFFFF")
    else: 
        bg_color = st.color_picker("배경색 선택", "#FFFFFF")
    
    show_box = st.checkbox("가독성 박스 추가(이미지 배경 시)", value=False)
    if show_box:
        bx_c = st.color_picker("바탕 박스 색상", "#FFFFFF")
        bx_o, bx_r = st.slider("바탕 투명도", 0, 100, 75), st.slider("바탕 모서리 곡률", 0, 100, 20)
    else: bx_c, bx_o, bx_r = "#FFFFFF", 75, 20
    
    st.markdown("---")
    st.info("4️⃣ **텍스트 설정**") # 순서 변경 💡 (기존 3번)
    lang = st.radio("언어", ["English", "한국어"], horizontal=True)
    font_f = st.selectbox("서체", ["Arial", "맑은 고딕", "바탕체", "나눔고딕"], index=0)
    is_bold = st.checkbox("볼드체 설정", value=False)
    with st.expander("외부 폰트 추가"):
        up_font = st.file_uploader("폰트 파일 (.ttf, .otf)", type=['ttf', 'otf'])
    
    t_color = st.color_picker("텍스트 색상", "#000000")
    f_size = st.slider("글자 크기", 10, 120, 30)
    with st.expander("📏 간격 세부 설정"):
        x_s, y_s = st.slider("가로 간격", 1.0, 5.0, 2.5), st.slider("세로 간격", 1.0, 5.0, 2.0)
    
    st.markdown("---")
    st.info("5️⃣ **출처 텍스트 표기**")
    # 체크란 이원화 💡
    show_moon1 = st.checkbox("제작자 표시 (Moon1)", value=False)
    show_custom = st.checkbox("싫어요 내 이름 적을꺼야", value=False)
    custom_text = ""
    if show_custom:
        custom_text = st.text_input("적고 싶은 문구 입력", value="내 이름")
    wm_color = st.color_picker("하단 글자 색상", "#000000")
    
    st.markdown("---")
    st.info("6️⃣ **초기화**")
    if st.button("🔄 모두 기본값으로"):
        for key in st.session_state.keys(): del st.session_state[key]
        st.rerun()

    st.caption("최종 수정: 2026.03.15.04.10")

# 결과 생성
final_img = generate_wallpaper(w, h, year, month, pos_val, bg_type, bg_color, bg_img, bg_rotate, bg_x, bg_y, bg_zoom, t_color, f_size, x_s, y_s, lang, font_f, up_font, is_bold, use_holidays, show_box, bx_c, bx_o, bx_r, show_moon1, show_custom, custom_text, wm_color)

st.markdown("### 미리보기")
st.image(final_img, width=450)
buf = io.BytesIO()
final_img.save(buf, format="PNG")
st.download_button("📥 이미지 파일로 저장", buf.getvalue(), f"calendar_{year}_{month}.png")
