# main.py
import streamlit as st
from llm import  process_image
from tools import enhance_image_quality, generate_report,file_to_base64,clean_temp_folder
import time
import json
import io

def main():

    
    
    st.set_page_config(page_title="Telecom Site Analyzer",page_icon="📡", layout="wide")

    
    # Custom CSS for styling
    st.markdown("""
    <style>
        .report-title { 
            color: #1e3c72;
            font-size: 2.5em;
            text-align: center;
        }
        .stProgress > div > div > div {
            background-color: #1e3c72;
        }
        .stSpinner > div {
            border-top-color: #1e3c72;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<h1 class="report-title">📡 Telecom Site Survey Analyzer</h1>', unsafe_allow_html=True)
    
    # Clean up old images before new uploads
    clean_temp_folder()  
    

    

    # File upload section
    with st.expander("📤 Upload Site Images", expanded=True):
        uploaded_files = st.file_uploader(
            "Select images (JPEG/PNG)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )
    
    if uploaded_files:
        total_images = len(uploaded_files)
        progress_bar = st.progress(0)
        status_container = st.empty()
        site_data = {
            "sections": {},
            "files": {}
        }
        
        with st.status("🔍 Starting Analysis...", expanded=True) as status:
            for index, img_file in enumerate(uploaded_files):
                current_progress = index / total_images
                progress_bar.progress(current_progress)
                
                # Update status
                status_container.markdown(f"""
                *Processing Image {index+1}/{total_images}*
                - File: {img_file.name}
                - Size: {img_file.size//1024} KB
                """)
                
                
                # Image enhancement
                with st.spinner("✨ Enhancing image quality..."):
                    enhanced_img = enhance_image_quality(img_file.read())
                    #file_path = save_uploaded_file(enhanced_img)  # Save locally
                    # Convert the uploaded file to base64
                    #base64_string = file_to_base64(enhanced_img)
                    time.sleep(0.2)  # Simulate processing
                
                # Image analysis
                with st.spinner("🤖 Analyzing site equipment..."):
                    analysis = process_image(
                        #chain=st.session_state.chain,
                        #image=enhanced_img,
                        #filename=img_file.name
                        image_bytes=enhanced_img
                    )
                    time.sleep(0.1)
                    if "error" in analysis:
                        st.error(f"❌ Error analyzing {img_file.name}: {analysis['error']}")
                        st.write(analysis['analysis'])
                        continue  # Skip this file if there's an error
                 # Extract section type and analysis data
                section_type = analysis.pop('destination', 'Miscellaneous')
                section_analysis = analysis.pop('analysis', '')
                
                # Store the data in site_data properly
                if section_type not in site_data["sections"]:
                    site_data["sections"][section_type] = []
                
                # Add analysis with file information
                analysis_entry = {
                    "filename": img_file.name,
                    "content": section_analysis,
                    # Store image bytes for report generation if needed
                    "image_bytes": enhanced_img
                }
                
                # Store in sections by type
                site_data["sections"][section_type].append(analysis_entry)
                
                # Also store by filename for easy lookup
                site_data["files"][img_file.name] = {
                    "type": section_type,
                    "content": section_analysis,
                    # Store image bytes for report generation if needed
                    "image_bytes": enhanced_img
                }

                # Display results in UI
                st.markdown(f"### 🔍 Analysis for {img_file.name}")
                
                # Reset file pointer for display
                img_stream = io.BytesIO(enhanced_img)

                # Use Streamlit columns to show the image and the analysis side by side
                col_img, col_text = st.columns([1, 2])
            
                with col_img:
                    st.image(img_file, caption=img_file.name)
                
                with col_text:
                    st.subheader(f"Analysis Details: {section_type}")
                    # Format the output nicely as text
                    st.markdown(section_analysis, unsafe_allow_html=True)
                    #st.text_area(label="Analysis,value=section_analysis,height=300)
                
                # Update progress
                progress_bar.progress((index+1) / total_images)
            
            # Final report generation
            status_container.markdown("📊 Compiling final report...")
            with st.spinner("📄 Generating reports..."):
                report_files = generate_report(site_data)
                time.sleep(0.3)
            
            status.update(label="✅ Analysis Complete!", state="complete", expanded=False)
        
        # Download section
        st.success("✨ Analysis finished successfully!")
        st.balloons()
        
        col1, col2, col3 = st.columns([2,3,2])
        with col2:
            st.markdown("### 📥 Download Reports")
            dl_col1, dl_col2 = st.columns(2)
            
            with dl_col1:
                st.download_button(
                    label="📝 Word Report",
                    data=report_files["docx"],
                    file_name="site_report.docx",
                    mime="application/octet-stream",
                    help="Detailed technical report in Word format"
                )
            
            

if __name__ == "__main__":
    main()