import streamlit as st
import yt_dlp
import os
import shutil

# تشخیص محیط (لپ‌تاپ یا سرور ابری)
IS_LOCAL = os.path.exists("ffmpeg.exe")

if IS_LOCAL:
    PROXY_URL = "socks5://127.0.0.1:10808"
else:
    PROXY_URL = None

DOWNLOAD_DIR = "Cloud_Downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

st.set_page_config(page_title="دانلودر من", page_icon="☁️", layout="centered")
st.title("☁️ دانلودر ابری (با کوکی)")

url = st.text_input("🔗 لینک ویدیو:")

# چک کردن وجود فایل کوکی
COOKIE_FILE = "cookies.txt"
if not os.path.exists(COOKIE_FILE):
    st.warning("⚠️ فایل cookies.txt پیدا نشد! احتمال ارور 403 روی سرور زیاد است.")

@st.cache_data(show_spinner=False)
def get_formats(link):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
        # اضافه کردن کوکی برای دور زدن تحریم یوتیوب
        'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None
    }
    if IS_LOCAL:
        ydl_opts['proxy'] = PROXY_URL

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            formats = info.get('formats', [])
            available = set()
            for f in formats:
                if f.get('height'):
                    available.add(f['height'])
            return sorted([q for q in available if q in [360, 480, 720, 1080]])
    except Exception as e:
        return None

if st.button("🔎 بررسی"):
    if not url:
        st.error("لینک را وارد کنید")
    else:
        with st.spinner("در حال اتصال..."):
            qualities = get_formats(url)
            if qualities:
                st.session_state['qualities'] = qualities
                st.session_state['url'] = url
                st.success("✅ متصل شد!")
            else:
                st.error("❌ خطا: یوتیوب اجازه دسترسی نداد (کوکی چک شود).")

if 'qualities' in st.session_state and st.session_state['url'] == url:
    quality = st.selectbox("کیفیت:", st.session_state['qualities'], index=len(st.session_state['qualities'])-1)
    
    if st.button("⬇️ دانلود"):
        progress_bar = st.progress(0)
        status = st.empty()
        
        format_str = f'bestvideo[height={quality}]+bestaudio/best[height={quality}]/best'
        out_tmpl = f'{DOWNLOAD_DIR}/%(title)s.%(ext)s'
        
        ydl_opts = {
            'format': format_str,
            'outtmpl': out_tmpl,
            'quiet': True,
            'nocheckcertificate': True,
            'merge_output_format': 'mp4',
            # استفاده حیاتی از کوکی در هنگام دانلود
            'cookiefile': COOKIE_FILE if os.path.exists(COOKIE_FILE) else None
        }
        
        if IS_LOCAL:
            ydl_opts['proxy'] = PROXY_URL
            ydl_opts['ffmpeg_location'] = '.'
        
        try:
            status.text("⏳ در حال دانلود...")
            progress_bar.progress(20)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                final_filename = os.path.splitext(filename)[0] + ".mp4"
            
            progress_bar.progress(100)
            status.text("✅ تمام شد!")
            
            with open(final_filename, "rb") as file:
                st.download_button(
                    label="💾 ذخیره فایل",
                    data=file,
                    file_name=os.path.basename(final_filename),
                    mime="video/mp4"
                )
                
        except Exception as e:
            st.error(f"خطا: {e}")
