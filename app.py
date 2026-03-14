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

def generate_wallpaper(width, height, year, month, pos_ratio, bg_type, bg_color, bg_image,
                       bg_rotate, bg_x, bg_y, # 💡 배경 조작 매개변수 추가
                       text_color_hex, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold,
                       use_holidays, show_box, box_color_hex, box_opacity, box_radius,
                       show_watermark):
    
    # 1. 배경 이미지 조작 💡
    if bg_type == "이미지 업로드" and bg_image is not None:
        img = Image.open(bg_image).convert("RGBA")
        
        # 회전 적용
        img = img.rotate(bg_rotate, expand=True)
        
        # 크기 조정 (배경을 꽉 채우도록)
        # expand=True로 회전하면 크기가 커지므로, fits() 전에 크기 재설정
        width_ratio = width / img.width
        height_ratio = height / img.height
        new_width = int(img.width * max(width_ratio, height_ratio))
        new_height = int(img.height * max(width_ratio, height_ratio))
        img = img.resize((new_width, new_height), resample=Image.LANCZOS)
        
        # 위치 이동 ( crop() 활용)
        # 이미지 중앙 기준으로 pos 설정
        center_x, center_y = new_width / 2, new_height / 2
        
        # 사용자가 설정한 비율(bg_x, bg_y)을 크기로 변환
        x_offset = int((bg_x / 100) * (new_width - width))
        y_offset = int((bg_y / 100) * (new_height - height))

        # crop 영역 계산
        left = int(center_x - width / 2) + x_offset
        top = int(center_y - height / 2) + y_offset
        right = left + width
        bottom = top + height
        
        # crop 적용
        img = img.crop((left, top, right, bottom))
        
        # crop 후 크기가 정확히 일치하는지 확인
        if img.size != (width, height):
            img = img.resize((width, height), resample=Image.LANCZOS)
        
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
        b_color = ImageColor.getrgb(box_color_hex)
        full_box_color = (b_color[0], b_color[1], b_color[2], int(255 * (box_opacity/100)))
        padding = 40
        draw.rounded_rectangle(
            [start_x - padding, start_y - padding, start_x + cal_width + padding, start_y + cal_height + padding],
            radius=box_radius, fill=full_box_color
        )

    draw.text((width/2, start_y + row_height/2), m_name, fill=text_color, font=bold_font, anchor="mm")
    
    header_y = start_y + (row_height * 2)
    for i, h in enumerate(headers):
        x = start_x + (i * col_width) + (col_width / 2)
        color = red_color if i == 0 else text_color
        draw.text((x, header_y), h, fill=color, font=reg_font, anchor="mm")

    for row_idx, week in enumerate(weeks):
        y = header_y + (row_height * (row_idx + 1))
        for col_idx, day in enumerate(week):
            if day != 0:
                x = start_x + (col_idx * col_width) + (col_width / 2)
                is_h = date(year, month, day) in kr_holidays
                color = red_color if (col_idx == 0 or is_h) else text_color
                draw.text((x, y), str(day), fill=color, font=reg_font, anchor="mm")

    if show_watermark:
        small_bold_font = get_font(font_family, uploaded_font, 20, lang, force_bold=True)
        draw.text((width - 30, height - 30), "Moon1", fill=text_color, font=small_bold_font, anchor="rd")

    return Image.alpha_composite(img, overlay).convert("RGB")

# --- UI 레이아웃 ---
st.set_page_config(page_title="달력 배경화면 생성기", layout="wide")

st.markdown("<h2 style='margin-top: 0px;'>📅 달력 배경화면 생성기</h2>", unsafe_allow_html=True)

with st.sidebar:
    st.header("1. 기기 규격 설정")
    category = st.selectbox("기기 분류", 
                            ["스마트폰 (1080x2340)", "태블릿 (2048x2732)", "이북 리더기 (758x1024)", "직접 입력"],
                            index=2)
    
    res_map = {
        "스마트폰 (1080x2340)": (1080, 2340),
        "태블릿 (2048x2732)": (2048, 2732),
        "이북 리더기 (758x1024)": (758, 1024)
    }
    
    if category == "직접 입력":
        w, h = st.number_input("가로", value=1080), st.number_input("세로", value=1920)
    else:
        w, h = res_map[category]

    st.header("2. 날짜 및 위치")
    c1, c2 = st.columns(2)
    year, month = c1.number_input("년", value=2026), c2.number_input("월", 1, 12, 3)
    is_landscape = st.checkbox("🔄 가로로 돌리기 (가로 모드)", value=False)
    if is_landscape: w, h = h, w
    use_holidays = st.checkbox("대한민국 공휴일 반영", value=True)
    pos_val = st.slider("세로 위치 (%)", 0, 100, 50)

    st.header("3. 달력 디자인")
    lang = st.radio("언어", ["English", "한국어"], horizontal=True)
    font_family = st.selectbox("서체", ["Arial", "맑은 고딕", "바탕체", "나눔고딕"], index=0)
    is_bold = st.checkbox("볼드체 설정", value=False)
    uploaded_font = st.file_uploader("외부 폰트 추가 (.ttf, .otf)", type=['ttf', 'otf'])
    text_color = st.color_picker("텍스트 색상", "#000000")
    
    font_size = st.slider("글자 크기", 10, 120, 40)
    x_spacing = st.slider("가로 간격 (격자 넓이)", 1.0, 5.0, 2.5, step=0.1)
    y_spacing = st.slider("세로 간격 (격자 높이)", 1.0, 5.0, 2.0, step=0.1)

    st.header("4. 배경 설정")
    bg_type = st.radio("배경", ["단색 컬러", "이미지 업로드"], horizontal=True, index=0)
    
    # 💡 배경 이미지 조작 설정 추가
    bg_rotate = 0
    bg_x = 0
    bg_y = 0
    
    if bg_type == "이미지 업로드":
        bg_image = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
        bg_color = "#FFFFFF"
        
        if bg_image is not None:
            # 이미지 조작 설정
            with st.expander("배경 이미지 조작 (회전, 위치)", expanded=True):
                bg_rotate = st.slider("회전 (도)", 0, 360, 0, step=90)
                bg_x = st.slider("가로 위치 (%)", -100, 100, 0)
                bg_y = st.slider("세로 위치 (%)", -100, 100, 0)
    else:
        bg_color = st.color_picker("배경색 선택", "#FFFFFF")
        bg_image = None
    
    st.markdown("---")
    # 가독성 박스 명칭 수정💡
    show_box = st.checkbox("가독성 박스 추가(이미지 배경 시)", value=False)
    box_color = st.color_picker("바탕 색상", "#FFFFFF")
    box_opacity = st.slider("바탕 투명도", 0, 100, 100)
    box_radius = st.slider("바탕 모서리 곡률", 0, 100, 20)

    st.header("5. 제작자 출처 표기")
    show_watermark = st.checkbox("Moon1 마크 표시 (우측 하단)", value=False)

# 결과 생성
final_img = generate_wallpaper(w, h, year, month, pos_val, bg_type, bg_color, bg_image,
                               bg_rotate, bg_x, bg_y, # 💡 배경 조작 매개변수 추가
                               text_color, font_size, x_spacing, y_spacing, lang, font_family, uploaded_font, is_bold,
                               use_holidays, show_box, box_color, box_opacity, box_radius,
                               show_watermark)

st.markdown("### 미리보기")
buf = io.BytesIO()
final_img.save(buf, format="PNG")
st.image(buf.getvalue(), width=400)
st.download_button("📥 이미지 파일로 저장", buf.getvalue(), f"calendar_{year}_{month}.png")
