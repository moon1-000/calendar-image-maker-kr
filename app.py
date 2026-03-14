st.header("4. 배경 설정")
    bg_type = st.radio("배경", ["단색 컬러", "이미지 업로드"], horizontal=True, index=0)
    
    # 💡 변수 초기화 (에러 방지)
    bg_rotate = 0
    bg_x = 0
    bg_y = 0
    bg_image = None
    
    if bg_type == "이미지 업로드":
        bg_image = st.file_uploader("이미지 업로드", type=['jpg', 'png', 'jpeg'])
        bg_color = "#FFFFFF"
        
        # 💡 사진을 올리면 바로 조작 메뉴가 보이게 하되, 
        # 사용자가 "여기서 조절하는구나"를 알 수 있게 안내 문구 추가
        if bg_image is not None:
            st.info("💡 아래 슬라이더로 사진의 위치와 방향을 조절하세요.")
            bg_rotate = st.slider("회전 (도)", 0, 360, 0, step=90)
            bg_x = st.slider("가로 위치 미세 조정", -100, 100, 0)
            bg_y = st.slider("세로 위치 미세 조정", -100, 100, 0)
        else:
            st.warning("먼저 이미지를 업로드해 주세요.")
            
    else:
        bg_color = st.color_picker("배경색 선택", "#FFFFFF")
