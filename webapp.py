import streamlit as st
import yt_dlp
import os
import shutil

# -----------------------------------
# تنظیمات هوشمند
# -----------------------------------
# بررسی اینکه آیا روی سرور ابری هستیم یا لپ‌تاپ؟
# اگر پوشه ffmpeg.exe نباشد، فرض می‌کنیم روی سرور لینوکس هستیم
IS_LOCAL = os.path.exists("ffmpeg.exe")

if IS_LOCAL:
    # تنظیمات لپ‌تاپ (با پروکسی و فایل exe)
    PROXY_URL = "socks5://127.0.0.1:10808"
    FFMPEG_LOC = '.'
else:
    # تنظیمات سرور ابری (بدون پروکسی، ffmpeg سیستمی)
    PROXY_URL = None
    FFMPEG_LOC = None  # خودش از سیستم پیدا می‌کند

DOWNLOAD_DIR = "Cloud_Downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# تنظیمات صفحه
st.set_page_config(page_title="دانلودر من", page_icon="☁️", layout="centered")
st.title("☁️ دانلودر ابری (همیشه آنلاین)")

# ورودی لینک
url = st.text_input("🔗 لینک ویدیو:")

@st.cache_data(show_spinner=False)
def get_formats(link):
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'nocheckcertificate': True,
    }
    # فقط اگر لوکال بودیم پروکسی بزن
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
        st.error("لینک بدهید!")
    else:
        with st.spinner("در حال اتصال به یوتیوب..."):
            qualities = get_formats(url)
            if qualities:
                st.session_state['qualities'] = qualities
                st.session_state['url'] = url
                st.success("✅ پیدا شد!")
            else:
                st.error("❌ خطا (احتمالا آی‌پی سرور محدود شده است)")

if 'qualities' in st.session_state and st.session_state['url'] == url:
    quality = st.selectbox("کیفیت:", st.session_state['qualities'], index=len(st.session_state['qualities'])-1)
    
    if st.button("⬇️ دانلود کن"):
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
        }
        
        if IS_LOCAL:
            ydl_opts['proxy'] = PROXY_URL
            ydl_opts['ffmpeg_location'] = '.'
        
        try:
            status.text("⏳ در حال پردازش در ابر...")
            progress_bar.progress(20)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                final_filename = os.path.splitext(filename)[0] + ".mp4"
            
            progress_bar.progress(100)
            status.text("✅ آماده شد!")
            
            with open(final_filename, "rb") as file:
                st.download_button(
                    label="💾 ذخیره در گوشی",
                    data=file,
                    file_name=os.path.basename(final_filename),
                    mime="video/mp4"
                )
                
        except Exception as e:
            st.error(f"خطا: {e}")