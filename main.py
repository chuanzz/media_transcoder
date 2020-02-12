#!/usr/bin/env python
# coding: utf-8

# In[1]:


import os
import subprocess
from tqdm import tqdm
import json


# In[2]:


with open('./config.ini', 'r', encoding='utf-8') as file:
    exec(file.read())


# In[3]:


def popen_exec(command):
    popen = subprocess.Popen(command,
                             stdout = subprocess.PIPE,
                             stderr = subprocess.PIPE,
                             )
    
    out, err = popen.communicate()
    log = out.decode(current_encoding)
    err = err.decode(current_encoding)
    log+=('\n##err##\n' + err) if err else ''
    return log

def write(path,content):
    with open(path, 'w') as file_object:
        file_object.write(content)


# In[4]:


file_list_res = []
def file_list(dir):
    #列出文件夹下文件
    global file_list_res
    list = os.listdir(dir) 
    for i in range(0,len(list)):
        path = os.path.join(dir,list[i])
        if os.path.isfile(path):
            file_list_res.append(path)
        else:
            file_list(path)
    return file_list_res

def trans_list(dir):
    #列出文件夹下符合条件视频目录
    videos = []
    imgs = []
    for trans_path in file_list(dir):
        if trans_path.find('_transcoded') != -1:
            continue
        file_size = os.path.getsize(trans_path)
        if (file_size/(1024**3-1) > file_size_line) and trans_path.lower().endswith(video_format[0]):
            out_trans_path, out_info_path = transcoded_path(trans_path, video_format[1])
            if os.path.exists(out_trans_path) or os.path.exists(out_info_path):
                continue
            else:
                videos.append(os.path.abspath(trans_path))
        elif trans_path.lower().endswith(img_format[0]):
            out_trans_path, out_info_path = transcoded_path(trans_path, img_format[1])
            if os.path.exists(out_trans_path) or os.path.exists(out_info_path):
                continue
            else:
                imgs.append(os.path.abspath(trans_path))
            
    return (videos, imgs)

def transcoded_path(path,suffix):
    s = path.rfind('.')
    out_trans_path = path[0:s]+'_transcoded'+suffix
    out_info_path = path[0:s]+'_transcoded.log'
    return (out_trans_path, out_info_path)


# In[5]:


def get_video_info(trans_path):
    #获取视频fps和宽度
    para = [
        '-v', 'quiet',
        '-print_format','json',
        #'-show_format',
        '-show_streams',
    ]
    trans_streams = popen_exec([ffmpeg_dir+"ffprobe", "-i", trans_path] + para)
    trans_streams = json.loads(trans_streams)['streams'][0]
    
    fps = trans_streams['r_frame_rate']
    fps = eval(fps)
    width = trans_streams['width']
    
    return (fps,width)

def handle_video(trans_path,out_trans_path):
    fps, width = get_video_info(trans_path)
    
    para = [
        '-c:v',trans_format,
        '-y'if overwrite else '-n'
    ]
    if width > width_line:
        para+=['-vf','scale={}:-1'.format(width_line)]
    if fps > fps_line:
        para+=['-r',str(fps_line)]

    out = popen_exec([ffmpeg_dir+"ffmpeg", "-i", trans_path] + para + [out_trans_path])
    return out
    
def handle_img(trans_path,out_trans_path):
    para = [
        '-y'if overwrite else '-n'
    ]

    out = popen_exec([ffmpeg_dir+"ffmpeg", "-i", trans_path] + para + [out_trans_path])
    return out
    
def handle(trans_paths, trans_type):
    for trans_path in tqdm(trans_paths,desc=trans_type):
        
        if trans_type == "img":
            out_trans_path, out_info_path = transcoded_path(trans_path, img_format[1])
            out = handle_img(trans_path,out_trans_path)
        elif trans_type == "video":
            out_trans_path, out_info_path = transcoded_path(trans_path, video_format[1])
            out = handle_video(trans_path,out_trans_path)
               
        if generate_log_file:
            write(out_info_path, out)
        if remove_raw_file:
            os.remove(trans_path)
        


# In[6]:


if __name__ == "__main__":
    videos_paths, imgs_paths = trans_list(trans_dir)
    
    tqdm.write('program starting...')
    
    handle(imgs_paths, 'img') 
    handle(videos_paths, 'video')
    
    tqdm.write('done!')
