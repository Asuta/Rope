import os
import cv2
import tkinter as tk
from tkinter import filedialog, font
import numpy as np
from PIL import Image, ImageTk
import json
import time
import copy
import bisect
import torch
import torchvision
from send2trash import send2trash

torchvision.disable_beta_transforms_warning()
import mimetypes
import webbrowser
from random import random


import rope.GUIElements as GE
import rope.Styles as style

from skimage import transform as trans
from torchvision.transforms import v2

import inspect #print(inspect.currentframe().f_back.f_code.co_name, 'resize_image')

class GUI(tk.Tk):
    def __init__(self, models):  
        super().__init__()

        self.models = models
        self.title('Rope-Pearl-00')
        self.target_media = []
        self.target_video_file = []
        self.action_q = []
        self.video_image = []
        self.video_loaded = False
        self.image_loaded = False
        self.image_file_name = []
        self.stop_marker = []
        self.stop_image = []
        self.stop_marker_icon = []
        self.window_last_change = []
        self.blank = tk.PhotoImage()
        self.output_folder = []
        self.output_videos_text = []
        self.target_media_buttons = []
        self.input_videos_button = []
        self.input_videos_text = []
        self.target_media_canvas = []
        self.source_faces_buttons = []
        self.input_videos_button = []
        self.input_faces_text = []
        self.shift_i_len = 0
        self.source_faces_canvas = []
        self.video = []
        self.video_slider = []
        self.found_faces_canvas = []
        self.merged_embedding_name = []
        self.merged_embeddings_text = []
        self.me_name = []
        self.merged_faces_canvas = []
        self.parameters = {}
        self.control = {}        
        self.widget = {}
        self.static_widget = {}
        self.layer = {}


        self.temp_emb = []

        self.arcface_dst = np.array([[38.2946, 51.6963], [73.5318, 51.5014], [56.0252, 71.7366], [41.5493, 92.3655], [70.7299, 92.2041]], dtype=np.float32)


        self.json_dict =    {
                            "source videos":    None, 
                            "source faces":     None, 
                            "saved videos":     None, 
                            'dock_win_geom':    [1400, 800, self.winfo_screenwidth()/2-400, self.winfo_screenheight()/2-510],
                            }

        self.marker =  {
                        'frame':        '0',
                        'parameters':   '',
                        'icon_ref':     '',
                        }
        self.markers = []   

        self.target_face = {    
                            "TKButton":                 [],
                            "ButtonState":              "off",
                            "Image":                    [],
                            "Embedding":                [],
                            "SourceFaceAssignments":    [],
                            "EmbeddingNumber":          0,       #used for adding additional found faces
                            'AssignedEmbedding':        [],     #the currently assigned source embedding, including averaged ones
                            }
        self.target_faces = []
        
        self.source_face =  {
                            "TKButton":                 [],
                            "ButtonState":              "off",
                            "Image":                    [],
                            "Embedding":                []
                            }   
        self.source_faces = [] 
        self.bind('<Delete>', self.delete_selected_face)
        print("Delete键绑定已设置")
        self.bind('<Control-a>', self.select_all_faces)  # 添加这一行
        print("Delete键和Ctrl+A键绑定已设置")
   
                                                    

#####

    def select_all_faces(self, event):
        print("select_all_faces 方法被调用")
        for face in self.source_faces:
            face["ButtonState"] = True
            face["TKButton"].config(style.media_button_on_3)
        self.update_faces_canvas()
        print("所有faces已被选中并处理")
        self._update_target_face_assignments()
        
        # 更新target faces (如果需要的话)
        # self.update_target_faces()
        
    def delete_selected_face(self, event):
        print("delete_selected_face 方法被调用")
        for i, face in enumerate(self.source_faces):
            if face["ButtonState"]:
                print(f"找到选中的face: {i}")
                
                # 规范化文件路径
                file_path = os.path.normpath(face["file"])
                print(f"规范化后的文件路径: {file_path}")
                
                # 检查文件是否存在
                if not os.path.exists(file_path):
                    print(f"文件不存在: {file_path}")
                    return
                
                # 将文件发送到回收站
                try:
                    send2trash(file_path)
                    print(f"已将文件发送到回收站: {file_path}")
                except Exception as e:
                    print(f"发送文件到回收站时出错: {str(e)}")
                    return  # 如果操作失败，我们不应继续

                # 从列表中移除face
                self.source_faces.pop(i)
                print(f"已从source_faces列表中移除face {i}")

                # 更新画布，而不是重新加载
                self.update_faces_canvas()
                print("更新了faces画布")
                break
        else:
            print("没有找到选中的face")
            
    def update_faces_canvas(self):
        self.source_faces_canvas.delete("all")  # 清除画布上的所有内容
        
        for i, face in enumerate(self.source_faces):
            button_style = style.media_button_on_3 if face["ButtonState"] else style.media_button_off_3
            face["TKButton"] = tk.Button(self.source_faces_canvas, button_style, image=face["Image"], height=90, width=90)
            face["TKButton"].bind("<ButtonRelease-1>", lambda event, arg=i: self.select_input_faces(event, arg))
            face["TKButton"].bind("<MouseWheel>", self.source_faces_mouse_wheel)
            
            self.source_faces_canvas.create_window((i % 2) * 100, (i // 2) * 100, window=face["TKButton"], anchor='nw')
            # print(f"重新绘制了face {i}, 选中状态: {face['ButtonState']}")
        
        self.static_widget['input_faces_scrollbar'].resize_scrollbar(None)

    def create_gui(self):

        # 1 x 3 Top level grid
        self.grid_columnconfigure(0, weight=1)  
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)  
        self.grid_rowconfigure(2, weight=0)  
        
        self.configure(style.frame_style_bg)

        # Top Frame
        top_frame = tk.Frame(self, style.canvas_frame_label_1)
        top_frame.grid(row=0, column=0, sticky='NEWS', padx=1, pady=1)   
        top_frame.grid_columnconfigure(0, weight=1) 
        top_frame.grid_columnconfigure(1, weight=0) 
        
        # Middle Frame
        middle_frame = tk.Frame( self, style.frame_style_bg)
        middle_frame.grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        middle_frame.grid_rowconfigure(0, weight=1)         
        # Videos and Faces
        middle_frame.grid_columnconfigure(0, weight=0)
        # Preview
        middle_frame.grid_columnconfigure(1, weight=1)  
        # Parameters
        middle_frame.grid_columnconfigure(2, weight=0)   
        # Scrollbar
        middle_frame.grid_columnconfigure(3, weight=0)         
        
        # Bottom Frame
        bottom_frame = tk.Frame( self, style.canvas_frame_label_1)
        bottom_frame.grid(row=2, column=0, sticky='NEWS', padx=1, pady=1) 
        bottom_frame.grid_columnconfigure(0, minsize=100) 
        bottom_frame.grid_columnconfigure(1, weight=1)
        bottom_frame.grid_columnconfigure(2, minsize=100)
  
####### Top Frame    
      # Left
        # Label
        self.layer['topleft'] = tk.Frame(top_frame, style.canvas_frame_label_1, height = 42)
        self.layer['topleft'].grid(row=0, column=0, sticky='NEWS', pady=0) 

        # Buttons
        self.widget['StartButton'] = GE.Button(self.layer['topleft'], 'StartRope', 1, self.load_all, None, 'control', 10, 9, width=200)        
        self.widget['OutputFolderButton'] = GE.Button(self.layer['topleft'], 'OutputFolder', 1, self.select_save_video_path, None, 'control', x=240, y=1, width=190)     
        self.output_videos_text = GE.Text(self.layer['topleft'], '', 1, 240, 20, 190, 20)
        
      # Right
        self.layer['topright'] = tk.Frame(top_frame, style.canvas_frame_label_1, height=42, width=413)
        self.layer['topright'].grid(row=0, column=1, sticky='NEWS', pady=0) 
        self.control['ClearVramButton'] = GE.Button(self.layer['topright'], 'ClearVramButton', 1, self.clear_mem, None, 'control', x=5, y=9, width=85, height=20)
        self.static_widget['vram_indicator'] = GE.VRAM_Indicator(self.layer['topright'], 1, 300, 20, 100, 11)

####### Middle Frame  

    ### Videos and Faces
        self.layer['InputVideoFrame'] = tk.Frame(middle_frame, style.canvas_frame_label_3)
        self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)
        # Buttons
        self.layer['InputVideoFrame'].grid_rowconfigure(0, weight=0)
        # Input Media Canvas
        self.layer['InputVideoFrame'].grid_rowconfigure(1, weight=1)

        # Input Videos
        self.layer['InputVideoFrame'].grid_columnconfigure(0, weight=0)
        # Scrollbar
        self.layer['InputVideoFrame'].grid_columnconfigure(1, weight=0)
        # Input Faces Canvas
        self.layer['InputVideoFrame'].grid_columnconfigure(0, weight=0)
        # Scrollbar
        self.layer['InputVideoFrame'].grid_columnconfigure(1, weight=0)

      # Input Videos
        # Button Frame
        frame = tk.Frame(self.layer['InputVideoFrame'], style.canvas_frame_label_2, height = 42)
        frame.grid(row=0, column=0, columnspan = 2, sticky='NEWS', padx=0, pady=0)

        # Buttons
        self.widget['VideoFolderButton'] = GE.Button(frame, 'LoadTVideos', 2, self.select_video_path, None, 'control', 10, 1, width=195)
        self.input_videos_text = GE.Text(frame, '', 2, 10, 20, 190, 20)

        # Input Videos Canvas
        self.target_media_canvas = tk.Canvas(self.layer['InputVideoFrame'], style.canvas_frame_label_3, height=100, width=195)
        self.target_media_canvas.grid(row=1, column=0, sticky='NEWS', padx=10, pady=10)
        self.target_media_canvas.bind("<MouseWheel>", self.target_videos_mouse_wheel)
        self.target_media_canvas.create_text(8, 20, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Input Videos")

        # Scroll Canvas
        scroll_canvas = tk.Canvas(self.layer['InputVideoFrame'], style.canvas_frame_label_3, bd=0, )
        scroll_canvas.grid(row=1, column=1, sticky='NEWS', padx=0, pady=0)
        scroll_canvas.grid_rowconfigure(0, weight=1)
        scroll_canvas.grid_columnconfigure(0, weight=1)

        self.static_widget['input_videos_scrollbar'] = GE.Scrollbar_y(scroll_canvas, self.target_media_canvas)

      # Input Faces
        # Button Frame
        frame = tk.Frame(self.layer['InputVideoFrame'], style.canvas_frame_label_2, height = 42)
        frame.grid(row=0, column=2, columnspan = 2, sticky='NEWS', padx=0, pady=0)

        # Buttons
        self.widget['FacesFolderButton'] = GE.Button(frame, 'LoadSFaces', 2, self.select_faces_path, None, 'control', 10, 1, width=195)
        self.input_faces_text = GE.Text(frame, '', 2, 10, 20, 190, 20)

        # Scroll Canvas
        self.source_faces_canvas = tk.Canvas(self.layer['InputVideoFrame'], style.canvas_frame_label_3, height = 100, width=195)
        self.source_faces_canvas.grid(row=1, column=2, sticky='NEWS', padx=10, pady=10)
        self.source_faces_canvas.bind("<MouseWheel>", self.source_faces_mouse_wheel)
        self.source_faces_canvas.create_text(8, 20, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Input Faces")

        scroll_canvas = tk.Canvas(self.layer['InputVideoFrame'], style.canvas_frame_label_3, bd=0, )
        scroll_canvas.grid(row=1, column=3, sticky='NEWS', padx=0, pady=0)
        scroll_canvas.grid_rowconfigure(0, weight=1)
        scroll_canvas.grid_columnconfigure(0, weight=1)

        self.static_widget['input_faces_scrollbar'] = GE.Scrollbar_y(scroll_canvas, self.source_faces_canvas)
        # GE.Separator_y(scroll_canvas, 14, 0)
        GE.Separator_y(self.layer['InputVideoFrame'], 229, 0)
        GE.Separator_x(self.layer['InputVideoFrame'], 0, 41)

    ### Preview
        self.layer['preview_column'] = tk.Frame(middle_frame, style.canvas_bg)
        self.layer['preview_column'].grid(row=0, column=1, sticky='NEWS', pady=0)
        self.layer['preview_column'].grid_columnconfigure(0, weight=1)
        # Preview Data
        self.layer['preview_column'].grid_rowconfigure(0, weight=0)
        # Preview Window
        self.layer['preview_column'].grid_rowconfigure(1, weight=1)
        # Timeline
        self.layer['preview_column'].grid_rowconfigure(2, weight=0)
        # MArkers
        self.layer['preview_column'].grid_rowconfigure(3, weight=0)
        # Controls
        self.layer['preview_column'].grid_rowconfigure(4, weight=0)
        # Found Faces
        self.layer['preview_column'].grid_rowconfigure(5, weight=0)
        # Merged Faces
        self.layer['preview_column'].grid_rowconfigure(6, weight=0)

      # Preview Data
        preview_data = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height = 24)
        preview_data.grid(row=0, column=0, sticky='NEWS', pady=0)
        preview_data.grid_columnconfigure(0, weight=1)
        preview_data.grid_columnconfigure(1, weight=1)
        preview_data.grid_columnconfigure(2, weight=1)
        # preview_data.grid_columnconfigure(3, weight=1)
        preview_data.grid_rowconfigure(0, weight=0)



        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=100)
        frame.grid(row=0, column=0)
        self.widget['AudioButton'] = GE.Button(frame, 'Audio', 2, self.toggle_audio, None, 'control', x=0, y=0, width=100)

        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=100)
        frame.grid(row=0, column=1)
        self.widget['MaskViewButton'] = GE.Button(frame, 'MaskView', 2, self.toggle_maskview, None, 'control', x=0, y=0, width=100)

        frame = tk.Frame(preview_data, style.canvas_frame_label_2, height = 24, width=200)
        frame.grid(row=0, column=2)
        self.widget['PreviewModeTextSel'] = GE.TextSelection(frame, 'PreviewModeTextSel', '', 2, self.set_view, True, 'control', width=200, height=20, x=0, y=0, text_percent=1)


      # Preview Window
        self.video = tk.Label(self.layer['preview_column'], bg='black')
        self.video.grid(row=1, column=0, sticky='NEWS', padx=0, pady=0)
        self.video.bind("<MouseWheel>", self.iterate_through_merged_embeddings)
        self.video.bind("<ButtonRelease-1>", lambda event: self.toggle_play_video())

    # Videos
      # Timeline
        # Slider
        self.layer['slider_frame'] = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height=20)
        self.layer['slider_frame'].grid(row=2, column=0, sticky='NEWS', pady=0)
        self.video_slider = GE.Timeline(self.layer['slider_frame'], self.widget, self.temp_toggle_swapper, self.add_action)

        # Markers
        self.layer['markers_canvas'] = tk.Canvas(self.layer['preview_column'], style.canvas_frame_label_2, height = 20)
        self.layer['markers_canvas'].grid(row=3, column=0, sticky='NEWS')
        self.layer['markers_canvas'].bind('<Configure>', lambda e:self.update_marker(e.width))

        # self.create_ui_button('ToggleStop', marker_frame, 140, 2, width=36, height=36)

      # Controls
        self.layer['preview_frame'] = tk.Frame(self.layer['preview_column'], style.canvas_bg, height = 40)
        self.layer['preview_frame'].grid(row=4, column=0, sticky='NEWS')
        self.layer['preview_frame'].grid_columnconfigure(0, weight=0)
        self.layer['preview_frame'].grid_columnconfigure(1, weight=1)
        self.layer['preview_frame'].grid_columnconfigure(2, weight=0)
        self.layer['preview_frame'].grid_rowconfigure(0, weight=0)
        self.layer['preview_frame'].grid_rowconfigure(1, weight=0)

        # Left Side
        self.layer['play_controls_left'] = tk.Frame(self.layer['preview_frame'], style.canvas_frame_label_2, height=30, width=100 )
        self.layer['play_controls_left'].grid(row=0, column=0, sticky='NEWS', pady=0)
        self.widget['SaveImageButton'] = GE.Button(self.layer['play_controls_left'], 'SaveImageButton', 2, self.save_image, None, 'control', x=10, y=5, width=100)

        # Center
        cente_frame = tk.Frame(self.layer['preview_frame'], style.canvas_frame_label_2, height=30, )
        cente_frame.grid(row=0, column=1, sticky='NEWS', pady=0)
        cente_frame.grid_columnconfigure(0, weight=0)
        cente_frame.grid_rowconfigure(0, weight=0)

        play_control_frame = tk.Frame(cente_frame, style.canvas_frame_label_2, height=30, width=270  )
        play_control_frame.place(anchor="c", relx=.5, rely=.5)

        column = 0
        col_delta = 50
        self.widget['TLBegButton'] = GE.Button(play_control_frame, 'TLBeginning', 2, self.preview_control, 'q', 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLLeftButton'] = GE.Button(play_control_frame, 'TLLeft', 2, self.preview_control, 'a', 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLRecButton'] = GE.Button(play_control_frame, 'Record', 2, self.toggle_rec_video, None, 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLPlayButton'] = GE.Button(play_control_frame, 'Play', 2, self.toggle_play_video, None, 'control', x=column , y=2, width=20)
        column += col_delta
        self.widget['TLRightButton'] = GE.Button(play_control_frame, 'TLRight', 2, self.preview_control, 'd', 'control', x=column , y=2, width=20)

        # Right Side
        right_playframe = tk.Frame(self.layer['preview_frame'], style.canvas_frame_label_2, height=30, width=100 )
        right_playframe.grid(row=0, column=2, sticky='NEWS', pady=0)
        self.widget['AddMarkerButton'] = GE.Button(right_playframe, 'AddMarkerButton', 2, self.update_marker, 'add', 'control', x=0, y=5, width=20)
        self.widget['DelMarkerButton'] = GE.Button(right_playframe, 'DelMarkerButton', 2, self.update_marker, 'delete', 'control', x=25, y=5, width=20)
        self.widget['PrevMarkerButton'] = GE.Button(right_playframe, 'PrevMarkerButton', 2, self.update_marker, 'prev', 'control', x=50, y=5, width=20)
        self.widget['NextMarkerButton'] = GE.Button(right_playframe, 'NextMarkerButton', 2, self.update_marker, 'next', 'control', x=75, y=5, width=20)
        # self.widget['StopMarkerButton'] = GE.Button(right_playframe, 'StopMarkerButton', 2, self.update_marker, 'stop', 'control', x=100, y=5, width=20)

    # Images
        self.layer['image_controls'] = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height=80)
        self.layer['image_controls'].grid(row=2, column=0, rowspan=2, sticky='NEWS', pady=0)
        self.widget['SaveImageButton'] = GE.Button(self.layer['image_controls'], 'SaveImageButton', 2, self.save_image, None, 'control', x=10, y=5, width=100)
        self.widget['AutoSwapButton'] = GE.Button(self.layer['image_controls'], 'AutoSwapButton', 2, self.toggle_auto_swap, None, 'control', x=150, y=5, width=100)


        self.layer['image_controls'].grid_forget()

    # FaceLab
        self.layer['FaceLab_controls'] = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_2, height=80)
        self.layer['FaceLab_controls'].grid(row=2, column=0, rowspan=2, sticky='NEWS', pady=0)



        self.layer['FaceLab_controls'].grid_forget()


      # Found Faces
        ff_frame = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_1)
        ff_frame.grid(row=5, column=0, sticky='NEWS', pady=1)
        ff_frame.grid_columnconfigure(0, weight=0)
        ff_frame.grid_columnconfigure(1, weight=1)
        ff_frame.grid_rowconfigure(0, weight=0)

        # Buttons
        button_frame = tk.Frame(ff_frame, style.canvas_frame_label_2, height = 100, width = 112)
        button_frame.grid( row = 0, column = 0, )

        self.widget['FindFacesButton'] = GE.Button(button_frame, 'FindFaces', 2, self.find_faces, None, 'control', x=0, y=0, width=112, height=33)
        self.widget['ClearFacesButton'] = GE.Button(button_frame, 'ClearFaces', 2, self.clear_faces, None, 'control', x=0, y=33, width=112, height=33)
        self.widget['SwapFacesButton'] = GE.Button(button_frame, 'SwapFaces', 2, self.toggle_swapper, None, 'control', x=0, y=66, width=112, height=33)

        # Scroll Canvas
        self.found_faces_canvas = tk.Canvas(ff_frame, style.canvas_frame_label_3, height = 100 )
        self.found_faces_canvas.grid( row = 0, column = 1, sticky='NEWS')
        self.found_faces_canvas.bind("<MouseWheel>", self.target_faces_mouse_wheel)
        self.found_faces_canvas.create_text(8, 45, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Found Faces")

        self.static_widget['20'] = GE.Separator_y(ff_frame, 111, 0)



      # Merged Faces
        mf_frame = tk.Frame(self.layer['preview_column'], style.canvas_frame_label_1)
        mf_frame.grid(row=6, column=0, sticky='NEWS', pady=0)
        mf_frame.grid_columnconfigure(0, minsize=10)
        mf_frame.grid_columnconfigure(1, weight=1)
        mf_frame.grid_rowconfigure(0, weight=0)

        # Buttons
        button_frame = tk.Frame(mf_frame, style.canvas_frame_label_2, height = 100, width = 112)
        button_frame.grid( row = 0, column = 0, )

        self.widget['DelEmbedButton'] = GE.Button(button_frame, 'DelEmbed', 2, self.delete_merged_embedding, None, 'control', x=0, y=0, width=112, height=33)

        # Merged Embeddings Text
        self.merged_embedding_name = tk.StringVar()
        self.merged_embeddings_text = tk.Entry(button_frame, style.entry_2, textvariable=self.merged_embedding_name)
        self.merged_embeddings_text.place(x=8, y=37, width = 96, height=20)
        self.merged_embeddings_text.bind("<Return>", lambda event: self.save_selected_source_faces(self.merged_embedding_name))
        self.me_name = self.nametowidget(self.merged_embeddings_text)

        # Scroll Canvas
        self.merged_faces_canvas = tk.Canvas(mf_frame, style.canvas_frame_label_3, height = 100)
        self.merged_faces_canvas.grid( row = 0, column = 1, sticky='NEWS')
        self.merged_faces_canvas.grid_rowconfigure(0, weight=1)
        self.merged_faces_canvas.bind("<MouseWheel>", lambda event: self.merged_faces_canvas.xview_scroll(-int(event.delta/120.0), "units"))
        self.merged_faces_canvas.create_text(8, 45, anchor='w', fill='grey25', font=("Arial italic", 20), text=" Merged Faces")
        self.static_widget['21'] = GE.Separator_y(mf_frame, 111, 0)

    ### Parameters
        width=398

        self.layer['parameter_frame'] = tk.Frame(middle_frame, style.canvas_frame_label_3, bd=0, width=width)
        self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

        self.layer['parameter_frame'].grid_rowconfigure(0, weight=0)
        self.layer['parameter_frame'].grid_rowconfigure(1, weight=1)
        self.layer['parameter_frame'].grid_rowconfigure(2, weight=0)
        self.layer['parameter_frame'].grid_columnconfigure(0, weight=0)
        self.layer['parameter_frame'].grid_columnconfigure(1, weight=0)

        parameters_control_frame = tk.Frame(self.layer['parameter_frame'], style.canvas_frame_label_2, bd=0, width=width, height = 42)
        parameters_control_frame.grid(row=0, column=0, columnspan=2, sticky='NEWS', pady=0, padx=0)
        parameters_control_frame.grid_columnconfigure(0, weight=1)
        parameters_control_frame.grid_columnconfigure(1, weight=1)
        parameters_control_frame.grid_columnconfigure(2, weight=1)
        parameters_control_frame.grid_rowconfigure(0, weight=0)


        frame = tk.Frame(parameters_control_frame, style.canvas_frame_label_2, height = 42, width=100)
        frame.grid(row=0, column=0)
        self.widget['SaveParamsButton'] = GE.Button(frame, 'SaveParamsButton', 2, self.parameter_io, 'save', 'control', x=0 , y=8, width=100)

        frame = tk.Frame(parameters_control_frame, style.canvas_frame_label_2, height = 42, width=100)
        frame.grid(row=0, column=1)
        self.widget['LoadParamsButton'] = GE.Button(frame, 'LoadParamsButton', 2, self.parameter_io, 'load', 'control', x=0 , y=8, width=100)

        frame = tk.Frame(parameters_control_frame, style.canvas_frame_label_2, height = 42, width=100)
        frame.grid(row=0, column=2)
        self.widget['DefaultParamsButton'] = GE.Button(frame, 'DefaultParamsButton', 2, self.parameter_io, 'default', 'control', x=0 , y=8, width=100)



        self.layer['parameters_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, width=width)
        self.layer['parameters_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)

        self.layer['parameters_frame'] = tk.Frame(self.layer['parameters_canvas'], style.canvas_frame_label_3, bd=0, width=width, height=1000)
        self.layer['parameters_frame'].grid(row=0, column=0, sticky='NEWS', pady=0, padx=0)

        self.layer['parameters_canvas'].create_window(0, 0, window = self.layer['parameters_frame'], anchor='nw')

        self.layer['parameter_scroll_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, )
        self.layer['parameter_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
        self.layer['parameter_scroll_canvas'].grid_rowconfigure(0, weight=1)
        self.layer['parameter_scroll_canvas'].grid_columnconfigure(0, weight=1)

        self.static_widget['parameters_scrollbar'] = GE.Scrollbar_y(self.layer['parameter_scroll_canvas'], self.layer['parameters_canvas'])

        self.static_widget['30'] = GE.Separator_x(parameters_control_frame, 0, 41)
        ### Layout ###
        top_border_delta = 25
        bottom_border_delta = 5
        switch_delta = 25
        row_delta = 20
        row = 1
        column = 160

        # Restore
        self.widget['RestorerSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'RestorerSwitch', 'Restorer', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['RestorerTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'RestorerTypeTextSel', 'Restorer Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['RestorerDetTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'RestorerDetTypeTextSel', 'Detection Alignment', 3, self.update_data, 'parameter', 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['RestorerSlider'] = GE.Slider2(self.layer['parameters_frame'], 'RestorerSlider', 'Blend', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['9'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Threshhold
        self.widget['ThresholdSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ThresholdSlider', 'Similarity Threshhold', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['3'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Orientation
        self.widget['OrientSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'OrientSwitch', 'Orientation', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['OrientSlider'] = GE.Slider2(self.layer['parameters_frame'], 'OrientSlider', 'Angle', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['2'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Strength
        self.widget['StrengthSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'StrengthSwitch', 'Strength', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['StrengthSlider'] = GE.Slider2(self.layer['parameters_frame'], 'StrengthSlider', 'Amount', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['5'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Border
        self.widget['BorderTopSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderTopSlider', 'Top Border Distance', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['BorderSidesSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderSidesSlider', 'Sides Border Distance', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['BorderBottomSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderBottomSlider', 'Bottom Border Distance', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['BorderBlurSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BorderBlurSlider', 'Border Blend', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['7'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Diff
        self.widget['DiffSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'DiffSwitch', 'Differencing', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['DiffSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DiffSlider', 'Amount', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['8'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Occluder
        self.widget['OccluderSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'OccluderSwitch', 'Occluder', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['OccluderSlider'] = GE.Slider2(self.layer['parameters_frame'], 'OccluderSlider', 'Size', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['10'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # FaceParser - Face
        self.widget['FaceParserSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'FaceParserSwitch', 'Face Parser', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['FaceParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceParserSlider', 'Background', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['MouthParserSlider'] = GE.Slider2(self.layer['parameters_frame'], 'MouthParserSlider', 'Mouth', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['12'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # CLIP
        self.widget['CLIPSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'CLIPSwitch', 'Text-Based Masking', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['CLIPTextEntry'] = GE.Text_Entry(self.layer['parameters_frame'], 'CLIPTextEntry', 'Text-Based Masking', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['CLIPSlider'] = GE.Slider2(self.layer['parameters_frame'], 'CLIPSlider', 'Amount', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['12'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Blur
        self.widget['BlendSlider'] = GE.Slider2(self.layer['parameters_frame'], 'BlendSlider', 'Overall Mask Blend', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['13'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Color Adjustments
        self.widget['ColorSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'ColorSwitch', 'Color Adjustments', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['ColorRedSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorRedSlider', 'Red', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['ColorGreenSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorGreenSlider', 'Green', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['ColorBlueSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorBlueSlider', 'Blue', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['ColorGammaSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ColorGammaSlider', 'Gamma', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['6'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # KPS Adjustment and scaling
        self.widget['FaceAdjSwitch'] = GE.Switch2(self.layer['parameters_frame'], 'FaceAdjSwitch', 'Input Face Adjustments', 3, self.update_data, 'parameter', 398, 20, 1, row)
        row += switch_delta
        self.widget['KPSXSlider'] = GE.Slider2(self.layer['parameters_frame'], 'KPSXSlider', 'KPS - X', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['KPSYSlider'] = GE.Slider2(self.layer['parameters_frame'], 'KPSYSlider', 'KPS - Y', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['KPSScaleSlider'] = GE.Slider2(self.layer['parameters_frame'], 'KPSScaleSlider', 'KPS - Scale', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['FaceScaleSlider'] = GE.Slider2(self.layer['parameters_frame'], 'FaceScaleSlider', 'Face Scale', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += top_border_delta
        self.static_widget['4'] = GE.Separator_x(self.layer['parameters_frame'], 0, row)
        row += bottom_border_delta

        # Cats and Dogs
        self.widget['ThreadsSlider'] = GE.Slider2(self.layer['parameters_frame'], 'ThreadsSlider', 'Threads', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)

        row += row_delta
        self.widget['DetectTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'DetectTypeTextSel', 'Detection Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['DetectScoreSlider'] = GE.Slider2(self.layer['parameters_frame'], 'DetectScoreSlider', 'Detect Score', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['RecordTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'RecordTypeTextSel', 'Record Type', 3, self.update_data, 'parameter', 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['VideoQualSlider'] = GE.Slider2(self.layer['parameters_frame'], 'VideoQualSlider', 'FFMPEG Quality', 3, self.update_data, 'parameter', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['MergeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'MergeTextSel', 'Merge Math', 3, self.select_input_faces, 'merge', '', 398, 20, 1, row, 0.62)
        row += row_delta
        self.widget['SwapperTypeTextSel'] = GE.TextSelection(self.layer['parameters_frame'], 'SwapperTypeTextSel', 'Swapper Resolution', 3, self.update_data, 'parameter', 'parameter', 398, 20, 1, row, 0.62)

    ### Other
        self.layer['tooltip_frame'] = tk.Frame(self.layer['parameter_frame'], style.canvas_frame_label_3, height=80)
        self.layer['tooltip_frame'].grid(row=2, column=0, columnspan=2, sticky='NEWS', padx=0, pady=0)
        self.layer['tooltip_label'] = tk.Label(self.layer['tooltip_frame'], style.info_label, wraplength=width-10, image=self.blank, compound='left', height=80, width=width-10)
        self.layer['tooltip_label'].place(x=5, y=5)
        self.static_widget['13'] = GE.Separator_x(self.layer['tooltip_frame'], 0, 0)
 ######### FaceLab

        self.layer['facelab_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, width=width)
        self.layer['facelab_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
        #
        self.layer['facelab_frame'] = tk.Frame(self.layer['facelab_canvas'], style.canvas_frame_label_3, bd=0, width=width, height=11000)
        self.layer['facelab_frame'].grid(row=0, column=0, sticky='NEWS', pady=0, padx=0)
        #
        self.layer['facelab_canvas'].create_window(0, 0, window=self.layer['facelab_frame'], anchor='nw')
        #
        self.layer['facelab_scroll_canvas'] = tk.Canvas(self.layer['parameter_frame'], style.canvas_frame_label_3, bd=0, )
        self.layer['facelab_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
        self.layer['facelab_scroll_canvas'].grid_rowconfigure(0, weight=1)
        self.layer['facelab_scroll_canvas'].grid_columnconfigure(0, weight=1)

        self.static_widget['facelab_scrollbar'] =GE.Scrollbar_y(self.layer['facelab_scroll_canvas'] , self.layer['facelab_canvas'])
        # row_delta = 20
        # row = 1
        # for i in range(512):
        #     temp_str = 'emb_vec_'+str(i)
        #     self.widget[temp_str] = GE.Slider3(self.layer['facelab_frame'], 'emb_vec_'+str(i), str(i), 3, self.adjust_embedding, i, 398, 20, 1, row, 0.62)
        #     row += row_delta

        ### Layout ###
        top_border_delta = 25
        bottom_border_delta = 5
        switch_delta = 25
        row_delta = 20
        row = 1
        column = 160
 ######### Options




        self.status_left_label = tk.Label(bottom_frame, style.donate_1, cursor="hand2", text=" Questions/Help/Discussions (Discord)")
        self.status_left_label.grid( row = 0, column = 0, sticky='NEWS')
        self.status_left_label.bind("<Button-1>", lambda e: self.callback("https://discord.gg/EcdVAFJzqp"))


        self.status_label = tk.Label(bottom_frame, style.donate_1, text="Rope Github")
        self.status_label.grid( row = 0, column = 1, sticky='NEWS')
        self.status_label.bind("<Button-1>", lambda e: self.callback("https://github.com/Hillobar/Rope"))

        self.donate_label = tk.Label(bottom_frame, style.donate_1, text="Enjoy Rope? Please Support! (Paypal) ", anchor='e')
        self.donate_label.grid( row = 0, column = 2, sticky='NEWS')
        self.donate_label.bind("<Button-1>", lambda e: self.callback("https://www.paypal.com/donate/?hosted_button_id=Y5SB9LSXFGRF2"))






    # Update the parameters or controls dicts and get a new frame
    def update_data(self, mode, name, use_markers=False):
        # print(inspect.currentframe().f_back.f_code.co_name,)
        if mode=='parameter':
            self.parameters[name] = self.widget[name].get()
            self.add_action('parameters', self.parameters)

        elif mode=='control':
            self.control[name] =  self.widget[name].get()
            self.add_action('control', self.control)

        if use_markers:
            self.add_action('get_requested_video_frame', self.video_slider.get())
        else:
            self.add_action('get_requested_video_frame_without_markers', self.video_slider.get())

    def callback(self, url):
        webbrowser.open_new_tab(url)

    def target_faces_mouse_wheel(self, event):
        self.found_faces_canvas.xview_scroll(1*int(event.delta/120.0), "units")


    def source_faces_mouse_wheel(self, event):
        self.source_faces_canvas.yview_scroll(-int(event.delta/120.0), "units")

        # Center of visible canvas as a percentage of the entire canvas
        center = (self.source_faces_canvas.yview()[1]-self.source_faces_canvas.yview()[0])/2
        center = center+self.source_faces_canvas.yview()[0]
        self.static_widget['input_faces_scrollbar'].set(center)


    def target_videos_mouse_wheel(self, event):
        self.target_media_canvas.yview_scroll(-int(event.delta/120.0), "units")

        # Center of visible canvas as a percentage of the entire canvas
        center = (self.target_media_canvas.yview()[1]-self.target_media_canvas.yview()[0])/2
        center = center+self.target_media_canvas.yview()[0]
        self.static_widget['input_videos_scrollbar'].set(center)


    def parameters_mouse_wheel(self, event):
        self.canvas.yview_scroll(1*int(event.delta/120.0), "units")


    # focus_get()
    def preview_control(self, event):
        # print(event.char, event.keysym, event.keycode)
        # print(type(event))
        if isinstance(event, str):
            event = event
        else:
            event = event.char


        if self.focus_get() !=  self.widget['CLIPTextEntry'] and self.focus_get() != self.merged_embeddings_text:


            if self.video_loaded:
                frame = self.video_slider.get()
                video_length = self.video_slider.get_length()
                if event == ' ':
                    self.toggle_play_video()
                elif event == 'w':
                    frame += 1
                    if frame > video_length:
                        frame = video_length
                    self.video_slider.set(frame)
                    self.add_action("get_requested_video_frame", frame)
                elif event == 's':
                    frame -= 1
                    if frame < 0:
                        frame = 0
                    self.video_slider.set(frame)
                    self.add_action("get_requested_video_frame", frame)
                elif event == 'd':
                    frame += 30
                    if frame > video_length:
                        frame = video_length
                    self.video_slider.set(frame)
                    self.add_action("get_requested_video_frame", frame)
                elif event == 'a':
                    frame -= 30
                    if frame < 0:
                        frame = 0
                    self.video_slider.set(frame)
                    self.add_action("get_requested_video_frame", frame)
                elif event == 'q':
                    frame = 0
                    self.video_slider.set(frame)
                    self.add_action("get_requested_video_frame", frame)



# refactor - make sure files are closed

    def initialize_gui( self ):
        json_object = {}
        # check if data.json exists, if not then create it, else load it
        try:
            data_json_file = open("data.json", "r")
        except:
            with open("data.json", "w") as outfile:
                json.dump(self.json_dict, outfile)
        else:
            json_object = json.load(data_json_file)
            data_json_file.close()

        # Window position and size
        try:
            self.json_dict['dock_win_geom'] = json_object['dock_win_geom']
        except:
            self.json_dict['dock_win_geom'] = self.json_dict['dock_win_geom']

        # Initialize the window sizes and positions
        self.geometry('%dx%d+%d+%d' % (self.json_dict['dock_win_geom'][0], self.json_dict['dock_win_geom'][1] , self.json_dict['dock_win_geom'][2], self.json_dict['dock_win_geom'][3]))
        self.window_last_change = self.winfo_geometry()

        self.bind('<Key>', lambda event: self.preview_control(event))
        self.bind('<space>', lambda event: self.preview_control(event))

        self.resizable(width=True, height=True)

        # Build UI, update ui with default data
        self.create_gui()

        self.video_image = cv2.cvtColor(cv2.imread('./rope/media/splash.png'), cv2.COLOR_BGR2RGB)
        self.resize_image()

        # Create parameters and controls and and selctively fill with UI data
        for key, value in self.widget.items():
            self.widget[key].add_info_frame(self.layer['tooltip_label'])
            if self.widget[key].get_data_type()=='parameter':
                self.parameters[key] = self.widget[key].get()


            elif self.widget[key].get_data_type()=='control':
                self.control[key] =  self.widget[key].get()

        try:
            self.json_dict["source videos"] = json_object["source videos"]
        except KeyError:
            self.widget['VideoFolderButton'].error_button()
        else:
            if self.json_dict["source videos"] == None:
                self.widget['VideoFolderButton'].error_button()
            else:
                path = self.create_path_string(self.json_dict["source videos"], 28)
                self.input_videos_text.configure(text=path)

        try:
            self.json_dict["source faces"] = json_object["source faces"]
        except KeyError:
            self.widget['FacesFolderButton'].error_button()
        else:
            if self.json_dict["source faces"] == None:
                self.widget['FacesFolderButton'].error_button()
            else:
                path = self.create_path_string(self.json_dict["source faces"], 28)
                self.input_faces_text.configure(text=path)

        try:
            self.json_dict["saved videos"] = json_object["saved videos"]
        except KeyError:
            self.widget['OutputFolderButton'].error_button()
        else:
            if self.json_dict["saved videos"] == None:
                self.widget['OutputFolderButton'].error_button()
            else:
                path = self.create_path_string(self.json_dict["saved videos"], 28)
                self.output_videos_text.configure(text=path)
                self.add_action("saved_video_path", self.json_dict["saved videos"])

        # Check for a user parameters file and load if present
        try:
            parameters_json_file = open("saved_parameters.json", "r")
        except:
            pass
        else:
            temp = json.load(parameters_json_file)
            parameters_json_file.close()
            for key, value in self.parameters.items():
                try:
                    self.parameters[key] = temp[key]
                except KeyError:
                    pass

              # Update the UI
            for key, value in self.parameters.items():
                self.widget[key].set(value, request_frame=False)

        self.add_action('parameters', self.parameters)
        self.add_action('control', self.control)


        self.widget['StartButton'].error_button()
        self.set_view(False, '')


    def create_path_string(self, path, text_len):
        if len(path)>text_len:
            last_folder = os.path.basename(os.path.normpath(path))
            last_folder_len = len(last_folder)
            if last_folder_len>text_len:
                path = path[:3]+'...'+path[-last_folder_len+6:]
            else:
                path = path[:text_len-last_folder_len]+'.../'+path[-last_folder_len:]

        return path

    def load_all(self):
        if not self.json_dict["source videos"] or not self.json_dict["source faces"]:
            print("Please set faces and videos folders first!")
            return

        self.populate_target_videos()
        self.load_input_faces()
        self.widget['StartButton'].enable_button()


    def select_video_path(self):
        temp = self.json_dict["source videos"]
        self.json_dict["source videos"] = filedialog.askdirectory(title="Select Target Videos Folder", initialdir=temp)

        path = self.create_path_string(self.json_dict["source videos"], 28)
        self.input_videos_text.configure(text=path)

        with open("data.json", "w") as outfile:
            json.dump(self.json_dict, outfile)
            outfile.close()
        self.widget['VideoFolderButton'].set(False, request_frame=False)
        self.populate_target_videos()

    def select_save_video_path(self):
        temp = self.json_dict["saved videos"]
        self.json_dict["saved videos"] = filedialog.askdirectory(title="Select Save Video Folder", initialdir=temp)

        path = self.create_path_string(self.json_dict["saved videos"], 28)
        self.output_videos_text.configure(text=path)

        with open("data.json", "w") as outfile:
            json.dump(self.json_dict, outfile)
            outfile.close()
        self.widget['OutputFolderButton'].set(False, request_frame=False)
        self.add_action("saved_video_path",self.json_dict["saved videos"])

    def select_faces_path(self):
        temp = self.json_dict["source faces"]
        self.json_dict["source faces"] = filedialog.askdirectory(title="Select Source Faces Folder", initialdir=temp)

        path = self.create_path_string(self.json_dict["source faces"], 28)
        self.input_faces_text.configure(text=path)

        with open("data.json", "w") as outfile:
            json.dump(self.json_dict, outfile)
            outfile.close()
        self.widget['FacesFolderButton'].set(False, request_frame=False)
        self.load_input_faces()

    def load_input_faces(self):
        print("load_input_faces 方法被调用")
        self.source_faces = []
        self.merged_faces_canvas.delete("all")
        self.source_faces_canvas.delete("all")

        # First load merged embeddings
        try:
            temp0 = []
            with open("merged_embeddings.txt", "r") as embedfile:
                temp = embedfile.read().splitlines()

                for i in range(0, len(temp), 513):
                    to = [temp[i][6:], np.array(temp[i+1:i+513], dtype='float32')]
                    temp0.append(to)

            for j in range(len(temp0)):
                new_source_face = self.source_face.copy()
                self.source_faces.append(new_source_face)

                self.source_faces[j]["ButtonState"] = False
                self.source_faces[j]["Embedding"] = temp0[j][1]
                self.source_faces[j]["TKButton"] = tk.Button(self.merged_faces_canvas, style.media_button_off_3, image=self.blank, text=temp0[j][0], height=14, width=84, compound='left')

                self.source_faces[j]["TKButton"].bind("<ButtonRelease-1>", lambda event, arg=j: self.select_input_faces(event, arg))
                self.source_faces[j]["TKButton"].bind("<MouseWheel>", lambda event: self.merged_faces_canvas.xview_scroll(-int(event.delta/120.0), "units"))

                self.merged_faces_canvas.create_window((j//4)*92,8+(22*(j%4)), window = self.source_faces[j]["TKButton"],anchor='nw')

            self.merged_faces_canvas.configure(scrollregion = self.merged_faces_canvas.bbox("all"))
            self.merged_faces_canvas.xview_moveto(0)

            print(f"加载了 {len(temp0)} 个合并的embeddings")
        except Exception as e:
            print(f"加载合并embeddings时出错: {str(e)}")

        self.shift_i_len = len(self.source_faces)

        # Next Load images
        directory = self.json_dict["source faces"]
        filenames = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(directory) for f in filenames]

        i=0
        for file in filenames:
            try:
                file_type = mimetypes.guess_type(file)[0][:5]
            except:
                print('无法识别的文件类型:', file)
            else:
                if file_type == 'image':
                    img = cv2.imread(file)

                    if img is not None:
                        img = torch.from_numpy(img.astype('uint8')).to('cuda')

                        pad_scale = 0.2
                        padded_width = int(img.size()[1]*(1.+pad_scale))
                        padded_height = int(img.size()[0]*(1.+pad_scale))

                        padding = torch.zeros((padded_height, padded_width, 3), dtype=torch.uint8, device='cuda:0')

                        width_start = int(img.size()[1]*pad_scale/2)
                        width_end = width_start+int(img.size()[1])
                        height_start = int(img.size()[0]*pad_scale/2)
                        height_end = height_start+int(img.size()[0])

                        padding[height_start:height_end, width_start:width_end,  :] = img
                        img = padding

                        img = img.permute(2,0,1)
                        try:
                            kpss = self.models.run_detect(img, max_num=1)[0] # Just one face here
                        except IndexError:
                            print('图像裁剪过近:', file)
                        else:
                            face_emb, cropped_image = self.models.run_recognize(img, kpss)
                            crop = cv2.cvtColor(cropped_image.cpu().numpy(), cv2.COLOR_BGR2RGB)
                            crop = cv2.resize(crop, (85, 85))

                            new_source_face = self.source_face.copy()
                            self.source_faces.append(new_source_face)

                            self.source_faces[-1]["Image"] = ImageTk.PhotoImage(image=Image.fromarray(crop))
                            self.source_faces[-1]["Embedding"] = face_emb
                            self.source_faces[-1]["TKButton"] = tk.Button(self.source_faces_canvas, style.media_button_off_3, image=self.source_faces[-1]["Image"], height=90, width=90)
                            self.source_faces[-1]["ButtonState"] = False
                            self.source_faces[-1]["file"] = file

                            self.source_faces[-1]["TKButton"].bind("<ButtonRelease-1>", lambda event, arg=len(self.source_faces)-1: self.select_input_faces(event, arg))
                            self.source_faces[-1]["TKButton"].bind("<MouseWheel>", self.source_faces_mouse_wheel)

                            self.source_faces_canvas.create_window((i % 2) * 100, (i // 2) * 100, window=self.source_faces[-1]["TKButton"], anchor='nw')

                            self.static_widget['input_faces_scrollbar'].resize_scrollbar(None)
                            i = i + 1
                            # print(f"加载了图像: {file}")

                    else:
                        print('无效的文件', file)

        torch.cuda.empty_cache()
        print(f"总共加载了 {i} 个图像文件")

    def find_faces(self):
        try:
            img = torch.from_numpy(self.video_image).to('cuda')
            img = img.permute(2,0,1)
            kpss = self.models.run_detect(img, max_num=50)


            ret = []
            for face_kps in kpss:

                # if kpss is not None:
                #     face_kps = kpss[i]


                face_emb, cropped_img = self.models.run_recognize(img, face_kps)
                ret.append([face_kps, face_emb, cropped_img])

        except Exception:
            print(" No media selected")

        else:
            # Find all faces and add to target_faces[]
            if ret:
                # Apply threshold tolerence
                threshhold = self.parameters["ThresholdSlider"]

                # if self.parameters["ThresholdState"]:
                    # threshhold = 0.0

                # Loop thgouh all faces in video frame
                for face in ret:
                    found = False

                    # Check if this face has already been found
                    for emb in self.target_faces:
                        if self.findCosineDistance(emb['Embedding'], face[1]) >= threshhold:
                            found = True
                            break

                    # If we dont find any existing simularities, it means that this is a new face and should be added to our found faces
                    if not found:
                        crop = cv2.resize(face[2].cpu().numpy(), (82, 82))

                        new_target_face = self.target_face.copy()
                        self.target_faces.append(new_target_face)
                        last_index = len(self.target_faces)-1

                        self.target_faces[last_index]["TKButton"] = tk.Button(self.found_faces_canvas, style.media_button_off_3, height = 86, width = 86)
                        self.target_faces[last_index]["TKButton"].bind("<MouseWheel>", self.target_faces_mouse_wheel)
                        self.target_faces[last_index]["ButtonState"] = False
                        self.target_faces[last_index]["Image"] = ImageTk.PhotoImage(image=Image.fromarray(crop))
                        self.target_faces[last_index]["Embedding"] = face[1]
                        self.target_faces[last_index]["EmbeddingNumber"] = 1

                        # Add image to button
                        self.target_faces[-1]["TKButton"].config( pady = 10, image = self.target_faces[last_index]["Image"], command=lambda k=last_index: self.toggle_found_faces_buttons_state(k))

                        # Add button to canvas
                        self.found_faces_canvas.create_window((last_index)*92, 8, window=self.target_faces[last_index]["TKButton"], anchor='nw')

                        self.found_faces_canvas.configure(scrollregion = self.found_faces_canvas.bbox("all"))

    def clear_faces(self):
        self.target_faces = []
        self.found_faces_canvas.delete("all")

    # toggle the target faces button and make assignments
    def toggle_found_faces_buttons_state(self, button):
        # Turn all Target faces off
        for i in range(len(self.target_faces)):
            self.target_faces[i]["ButtonState"] = False
            self.target_faces[i]["TKButton"].config(style.media_button_off_3)

        # Set only the selected target face to on
        self.target_faces[button]["ButtonState"] = True
        self.target_faces[button]["TKButton"].config(style.media_button_on_3)

        # set all source face buttons to off
        for i in range(len(self.source_faces)):
            self.source_faces[i]["ButtonState"] = False
            self.source_faces[i]["TKButton"].config(style.media_button_off_3)

        # turn back on the ones that are assigned to the curent target face
        for i in range(len(self.target_faces[button]["SourceFaceAssignments"])):
            self.source_faces[self.target_faces[button]["SourceFaceAssignments"][i]]["ButtonState"] = True
            self.source_faces[self.target_faces[button]["SourceFaceAssignments"][i]]["TKButton"].config(style.media_button_on_3)

    def select_input_faces(self, event, button):
        print(f"select_input_faces 被调用: event={event}, button={button}")
        
        if isinstance(event, str):
            modifier = event
        else:
            if event.state & 0x4 != 0:  # Ctrl键
                modifier = 'ctrl'
            elif event.state & 0x1 != 0:  # Shift键
                modifier = 'shift'
            else:
                modifier = 'none'
        print(f"修饰符: {modifier}")
        
        if modifier == 'ctrl':
            self._ctrl_select_face(button)
        elif modifier == 'shift':
            self._shift_select_faces(button)
        elif modifier == 'none':
            self._single_select_face(button)
        elif modifier == 'auto':
            self._auto_select_faces(button)
        
        self._update_target_face_assignments()

    def _ctrl_select_face(self, button):
        self.source_faces[button]["ButtonState"] = not self.source_faces[button]["ButtonState"]
        self.source_faces[button]["TKButton"].config(
            style.media_button_on_3 if self.source_faces[button]["ButtonState"] else style.media_button_off_3
        )
        print(f"切换了face {button}的ButtonState为: {self.source_faces[button]['ButtonState']}")


    def _select_all_faces(self):
        for face in self.source_faces:
            face["ButtonState"] = True
            face["TKButton"].config(style.media_button_on_3)
        print("执行了全选")

    def _shift_select_faces(self, end_button):
        start_button = next((i for i, face in enumerate(self.source_faces) if face["ButtonState"]), 0)
        for i in range(min(start_button, end_button), max(start_button, end_button) + 1):
            self.source_faces[i]["ButtonState"] = True
            self.source_faces[i]["TKButton"].config(style.media_button_on_3)
        print(f"激活了从face {start_button}到{end_button}的所有faces")

    def _single_select_face(self, button):
        for i, face in enumerate(self.source_faces):
            if i == button:
                face["ButtonState"] = not face["ButtonState"]
            else:
                face["ButtonState"] = False
            face["TKButton"].config(style.media_button_on_3 if face["ButtonState"] else style.media_button_off_3)
        print(f"切换了face {button}的ButtonState为: {self.source_faces[button]['ButtonState']}")

    def _auto_select_faces(self, button):
        # 保持现有的auto行为不变
        self.source_faces[button]["ButtonState"] = True
        self.source_faces[button]["TKButton"].config(style.media_button_on_3)

    def _update_target_face_assignments(self):
        for tface in self.target_faces:
            if tface["ButtonState"]:
                tface["SourceFaceAssignments"] = []
                temp_holder = []
                for j, face in enumerate(self.source_faces):
                    if face["ButtonState"]:
                        tface["SourceFaceAssignments"].append(j)
                        temp_holder.append(face['Embedding'])
                
                if temp_holder:
                    merge_method = self.widget['MergeTextSel'].get()
                    tface['AssignedEmbedding'] = np.median(temp_holder, 0) if merge_method == 'Median' else np.mean(temp_holder, 0)
                    self.temp_emb = tface['AssignedEmbedding']
                    print(f"使用{merge_method}合并了embeddings")
                break
        
        self.add_action("target_faces", self.target_faces)
        self.add_action('get_requested_video_frame', self.video_slider.get())
        print("添加了action: target_faces和get_requested_video_frame")


    def populate_target_videos(self):
        # Recursively read all media files from directory
        directory =  self.json_dict["source videos"]
        filenames = [os.path.join(dirpath,f) for (dirpath, dirnames, filenames) in os.walk(directory) for f in filenames]

        videos = []
        images = []
        self.target_media = []
        self.target_media_buttons = []
        self.target_media_canvas.delete("all")

        for file in filenames: # Does not include full path
            # Guess File type based on extension
            try:
                file_type = mimetypes.guess_type(file)[0][:5]
            except:
                print('Unrecognized file type:', file)
            else:
                # Its an image
                if file_type == 'image':
                    try:
                        image = cv2.imread(file)
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                    except:
                        print('Trouble reading file:', file)
                    else:
                        ratio = float(image.shape[0]) / image.shape[1]

                        new_height = 50
                        new_width = int(new_height / ratio)
                        image = cv2.resize(image, (new_width, new_height))
                        image[:new_height, :new_width, :] = image
                        images.append([image, file])

                # Its a video
                elif file_type == 'video':
                    try:
                        video = cv2.VideoCapture(file)
                    except:
                        print('Trouble reading file:', file)
                    else:
                        if video.isOpened():

                            # Grab a frame from the middle for a thumbnail
                            video.set(cv2.CAP_PROP_POS_FRAMES, int(video.get(cv2.CAP_PROP_FRAME_COUNT)/2))
                            success, video_frame = video.read()

                            if success:
                                video_frame = cv2.cvtColor(video_frame, cv2.COLOR_BGR2RGB)
                                ratio = float(video_frame.shape[0]) / video_frame.shape[1]

                                new_height = 50
                                new_width = int(new_height / ratio)
                                video_frame = cv2.resize(video_frame, (new_width, new_height))
                                video_frame[:new_height, :new_width, :] = video_frame

                                videos.append([video_frame, file])
                                video.release()

                            else:
                                print('Trouble reading file:', file)
                        else:
                            print('Trouble opening file:', file)
        delx, dely = 100, 79
        if self.widget['PreviewModeTextSel'].get()== 'Image':#images
            for i in range(len(images)):
                self.target_media_buttons.append(tk.Button(self.target_media_canvas, style.media_button_off_3, height = 86, width = 86))

                rgb_video = Image.fromarray(images[i][0])
                self.target_media.append(ImageTk.PhotoImage(image=rgb_video))
                self.target_media_buttons[i].config( image = self.target_media[i],  command=lambda i=i: self.load_target(i, images[i][1], self.widget['PreviewModeTextSel'].get()))
                self.target_media_buttons[i].bind("<MouseWheel>", self.target_videos_mouse_wheel)
                self.target_media_canvas.create_window((i%2)*delx, (i//2)*dely, window = self.target_media_buttons[i], anchor='nw')

            self.target_media_canvas.configure(scrollregion = self.target_media_canvas.bbox("all"))

        elif self.widget['PreviewModeTextSel'].get()=='Video':#videos

            for i in range(len(videos)):
                self.target_media_buttons.append(tk.Button(self.target_media_canvas, style.media_button_off_3, height = 65, width = 90))
                self.target_media.append(ImageTk.PhotoImage(image=Image.fromarray(videos[i][0])))

                filename = os.path.basename(videos[i][1])
                if len(filename)>14:
                    filename = filename[:11]+'...'

                self.target_media_buttons[i].bind("<MouseWheel>", self.target_videos_mouse_wheel)
                self.target_media_buttons[i].config(image = self.target_media[i], text=filename, compound='top', anchor='n',command=lambda i=i: self.load_target(i, videos[i][1], self.widget['PreviewModeTextSel'].get()))
                self.target_media_canvas.create_window((i%2)*delx, (i//2)*dely, window = self.target_media_buttons[i], anchor='nw')

            self.static_widget['input_videos_scrollbar'].resize_scrollbar(None)

    def auto_swap(self):
            # Reselect Target Image
            # try:
            self.find_faces()
            self.target_faces[0]["ButtonState"] = True
            self.target_faces[0]["TKButton"].config(style.media_button_on_3)

            # Reselect Source images
            self.select_input_faces('auto', '')
            self.toggle_swapper(True)
            # except:
            #     pass
    def toggle_auto_swap(self):
        self.widget['AutoSwapButton'].toggle_button()


    def load_target(self, button, media_file, media_type):
        # Make sure the video stops playing
        self.toggle_play_video('stop')
        self.image_loaded = False
        self.video_loaded = False
        self.clear_faces()

        if media_type == 'Video':
            self.video_slider.set(0)
            self.add_action("load_target_video", media_file)
            self.media_file_name = os.path.splitext(os.path.basename(media_file))
            self.video_loaded = True


        elif media_type == 'Image':
            self.add_action("load_target_image", media_file)
            self.media_file_name = os.path.splitext(os.path.basename(media_file))
            self.image_loaded = True

            # # find faces
            if self.widget['AutoSwapButton'].get():
                self.add_action('function', "gui.auto_swap()")




        for i in range(len(self.target_media_buttons)):
            self.target_media_buttons[i].config(style.media_button_off_3)

        self.target_media_buttons[button].config(style.media_button_on_3)

        # delete all markers
        self.layer['markers_canvas'].delete('all')
        self.markers = []
        self.stop_marker = []
        self.add_action("markers", self.markers)



    # @profile
    def set_image(self, image, requested):
        self.video_image = image[0]
        frame = image[1]

        if not requested:
            self.video_slider.set(frame)
            self.parameter_update_from_marker(frame)

        self.resize_image()

    # @profile
    def resize_image(self):
        image = self.video_image

        if len(image) != 0:

            x1 = float(self.video.winfo_width())
            y1 = float(self.video.winfo_height())


            x2 = float(image.shape[1])
            y2 = float(image.shape[0])


            m1 = x1/y1
            m2 = x2/y2

            if m2>m1:
                x2 = x1
                y2 = x1/m2
                image = cv2.resize(image, (int(x2), int(y2)))
                padding = int((y1-y2)/2.0)
                image = cv2.copyMakeBorder( image, padding, padding, 0, 0, cv2.BORDER_CONSTANT)
            else:
                y2=y1
                x2=y2*m2
                image = cv2.resize(image, (int(x2), int(y2)))
                padding=int((x1-x2)/2.0)
                image = cv2.copyMakeBorder( image, 0, 0, padding, padding, cv2.BORDER_CONSTANT)

            image = Image.fromarray(image)
            image = ImageTk.PhotoImage(image)
            self.video.image = image
            self.video.configure(image=self.video.image)





    def check_for_video_resize(self):

        # Read the geometry from the last time json was updated. json only updates once the window ahs stopped changing
        win_geom = '%dx%d+%d+%d' % (self.json_dict['dock_win_geom'][0], self.json_dict['dock_win_geom'][1] , self.json_dict['dock_win_geom'][2], self.json_dict['dock_win_geom'][3])

        # # window has started changing
        if self.winfo_geometry() != win_geom:
            # Resize image in video window
            self.resize_image()
            for k, v in self.widget.items():
                v.hide()
            for k, v in self.static_widget.items():
                v.hide()


            # Check if window has stopped changing
            if self.winfo_geometry() != self.window_last_change:
                self.window_last_change = self.winfo_geometry()

            # The window has stopped changing
            else:
                for k, v in self.widget.items():
                    v.unhide()
                for k, v in self.static_widget.items():
                    v.unhide()
                # Update json
                str1 = self.winfo_geometry().split('x')
                str2 = str1[1].split('+')
                win_geom = [str1[0], str2[0], str2[1], str2[2]]
                win_geom = [int(strings) for strings in win_geom]
                self.json_dict['dock_win_geom'] = win_geom
                with open("data.json", "w") as outfile:
                    json.dump(self.json_dict, outfile)





    def get_action(self):
        action = self.action_q[0]
        self.action_q.pop(0)
        return action

    def get_action_length(self):
        return len(self.action_q)



    def set_video_slider_length(self, video_length):
        self.video_slider.set_length(video_length)



    def findCosineDistance(self, vector1, vector2):
        cos_dist = 1 - np.dot(vector1, vector2)/(np.linalg.norm(vector1)*np.linalg.norm(vector2)) # 2..0
        return 100-cos_dist*50




    def toggle_play_video(self, set_value='toggle'):
        if self.video_loaded:

            # Update button
            if set_value == 'toggle':
                self.widget['TLPlayButton'].toggle_button()
            if set_value == 'stop':
                self.widget['TLPlayButton'].disable_button()
            if set_value == 'play':
                self.widget['TLPlayButton'].enable_button()

            # If play
            if self.widget['TLPlayButton'].get():
                if not self.video_loaded:
                    print("Please select video first!")
                    return
                else:
                    # and record
                    if self.widget['TLRecButton'].get():
                        if not self.json_dict["saved videos"]:
                            print("Set saved video folder first!")
                            self.add_action("play_video", "stop_from_gui")

                        else:
                            self.add_action("play_video", "record")

                    # only play
                    else:
                        self.add_action("play_video", "play")

            else:
                self.add_action("play_video", "stop_from_gui")


    def set_player_buttons_to_inactive(self):
        self.widget['TLRecButton'].disable_button()
        self.widget['TLPlayButton'].disable_button()


    def toggle_swapper(self, toggle_value=-1):
        # print(inspect.currentframe().f_back.f_code.co_name, 'toggle_swapper: '+'toggle_value='+str(toggle_value))

        if toggle_value == -1:
            self.widget['SwapFacesButton'].toggle_button()

        else:
            if toggle_value:
                self.widget['SwapFacesButton'].enable_button()
            else:
                self.widget['SwapFacesButton'].disable_button()

        if self.widget['PreviewModeTextSel'].get()=='Video' or self.widget['PreviewModeTextSel'].get()=='Theater':
            self.update_data('control', 'SwapFacesButton', use_markers=True)
        elif self.widget['PreviewModeTextSel'].get()=='Image':
            self.update_data('control', 'SwapFacesButton', use_markers=False)
        elif self.widget['PreviewModeTextSel'].get() == 'FaceLab':
            self.update_data('control', 'SwapFacesButton', use_markers=False)


    def temp_toggle_swapper(self, state):
        if state=='off':
            self.widget['SwapFacesButton'].temp_disable_button()
        elif state=='on':
            self.widget['SwapFacesButton'].temp_enable_button()

        self.update_data('control', 'SwapFacesButton', use_markers=True)

    def toggle_rec_video(self):
        # Play button must be off to enable record button
        if not self.widget['TLPlayButton'].get():
            self.widget['TLRecButton'].toggle_button()

            if self.widget['TLRecButton'].get():
                self.widget['TLRecButton'].enable_button()

            else:
                self.widget['TLRecButton'].disable_button()


    # this makes no sense
    def add_action(self, action, parameter=None): #
        # print(inspect.currentframe().f_back.f_code.co_name, '->add_action: '+action)

        if action != 'get_requested_video_frame' and action != 'get_requested_video_frame_without_markers':
            self.action_q.append([action, parameter])

        # Only do requests when the video is not playing - (moving the timeline or changing parameters)
        elif self.video_loaded and not self.widget['TLPlayButton'].get():
            self.action_q.append([action, parameter])

        elif self.image_loaded:
            self.action_q.append([action, parameter])

    def update_vram_indicator(self):
        try:
            used, total = self.models.get_gpu_memory()
        except:
            pass
        else:
            self.static_widget['vram_indicator'].set(used, total)



# refactor and thread i/o
    def save_selected_source_faces(self, text):
        # get name from text field
        text = text.get()
        # get embeddings from all highlightebuttons
        # iterate through the buttons

        temp_holder = []

        for button in self.source_faces:
            if button["ButtonState"]:
                temp_holder.append(button['Embedding'])

        if temp_holder:
            if self.widget['MergeTextSel'].get()=='Median':
                ave_embedding = np.median(temp_holder,0)
            elif self.widget['MergeTextSel'].get()=='Mean':
                ave_embedding = np.mean(temp_holder,0)

            for tface in self.target_faces:
                if tface["ButtonState"]:
                    ave_embedding = tface['AssignedEmbedding']

            if text != "":
                with open("merged_embeddings.txt", "a") as embedfile:
                    identifier = "Name: "+text
                    embedfile.write("%s\n" % identifier)
                    for number in ave_embedding:
                        embedfile.write("%s\n" % number)
            else:
                print('No embedding name specified')
        else:
            print('No Source Images selected')

        self.focus()
        self.load_input_faces()

# refactor and thread i/o
    def delete_merged_embedding(self): #add multi select

    # get selected button
        sel = []
        for j in range(len(self.source_faces)):
            if self.source_faces[j]["ButtonState"]:
                sel = j
                break

        # check if it is a merged embedding
        # if so, read txt embedding into list
        temp0 = []
        if os.path.exists("merged_embeddings.txt"):

            with open("merged_embeddings.txt", "r") as embedfile:
                temp = embedfile.read().splitlines()

                for i in range(0, len(temp), 513):
                    to = [temp[i], np.array(temp[i+1:i+513], dtype='float32')]
                    temp0.append(to)

        if j < len(temp0):
            temp0.pop(j)

            with open("merged_embeddings.txt", "w") as embedfile:
                for line in temp0:
                    embedfile.write("%s\n" % line[0])
                    for i in range(512):
                        embedfile.write("%s\n" % line[1][i])

        self.load_input_faces()

    def iterate_through_merged_embeddings(self, event):
        if event.delta>0:
            for i in range(len(self.source_faces)):
                if self.source_faces[i]["ButtonState"] and i<len(self.source_faces)-1:
                    self.select_input_faces('none', i+1)
                    break
        elif event.delta<0:
            for i in range(len(self.source_faces)):
                if self.source_faces[i]["ButtonState"]and i>0:
                    self.select_input_faces('none', i-1)
                    break

    def set_view(self, load_target_videos,b):
        # self.clear_faces()
        # self.video_loaded = False
        # self.image_loaded = False
        if load_target_videos and self.widget['PreviewModeTextSel'].get() != 'Theater':
            self.populate_target_videos()

        self.layer['slider_frame'].grid_forget()
        self.layer['preview_frame'].grid_forget()
        self.layer['markers_canvas'].grid_forget()
        self.layer['image_controls'].grid_forget()
        self.layer['FaceLab_controls'].grid_forget()
        self.layer['InputVideoFrame'].grid_forget()
        self.layer['parameter_frame'].grid_forget()

        self.layer['parameters_canvas'].grid_forget()
        self.layer['parameter_scroll_canvas'].grid_forget()

        self.layer['facelab_canvas'].grid_forget()
        self.layer['facelab_scroll_canvas'].grid_forget()

        if self.widget['PreviewModeTextSel'].get()=='Video':
            self.image_loaded = False
            self.layer['slider_frame'].grid(row=2, column=0, sticky='NEWS', pady=0)
            self.layer['preview_frame'].grid(row=4, column=0, sticky='NEWS')
            self.layer['markers_canvas'].grid(row=3, column=0, sticky='NEWS')
            self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

            self.layer['parameters_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
            self.layer['parameter_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
            self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)


        elif self.widget['PreviewModeTextSel'].get()=='Image':
            self.video_loaded = False
            self.layer['image_controls'].grid(row=2, column=0, rowspan=2, sticky='NEWS', pady=0)

            self.layer['parameters_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
            self.layer['parameter_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
            self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)
            self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)


        elif self.widget['PreviewModeTextSel'].get() == 'FaceLab':
            self.video_loaded = False
            self.layer['FaceLab_controls'].grid(row=2, column=0, rowspan=2, sticky='NEWS', pady=0)
            self.layer['facelab_canvas'].grid(row=1, column=0, sticky='NEWS', pady=0, padx=0)
            self.layer['facelab_scroll_canvas'].grid(row=1, column=1, sticky='NEWS', pady=0)
            self.layer['InputVideoFrame'].grid(row=0, column=0, sticky='NEWS', padx=1, pady=0)
            self.layer['parameter_frame'].grid(row=0, column=2, sticky='NEWS', pady=0, padx=1)

            # # find the input image with the lowest value
            # for face in self.source_faces:
            #     if face["ButtonState"]:
            #         self.image_loaded = True
            #         self.add_action("load_target_image", face["file"])
            #         break


        elif self.widget['PreviewModeTextSel'].get() == 'Theater':
            self.image_loaded = False
            self.layer['slider_frame'].grid(row=2, column=0, sticky='NEWS', pady=0)
            self.layer['preview_frame'].grid(row=4, column=0, sticky='NEWS')
            self.layer['markers_canvas'].grid(row=3, column=0, sticky='NEWS')





        
    def update_marker(self, action):

        if action=='add':
             # Delete existing marker at current frame and replace with new data
            for i in range(len(self.markers)):
                if self.markers[i]['frame'] == self.video_slider.get():
                    self.layer['markers_canvas'].delete(self.markers[i]['icon_ref'])
                    self.markers.pop(i)
                    break

            width = self.layer['markers_canvas'].winfo_width()-20-40-20
            position = 20+int(width*self.video_slider.get()/self.video_slider.get_length())

            temp_param = copy.deepcopy(self.parameters)            
            temp = {
                    'frame':        self.video_slider.get(),
                    'parameters':   temp_param,
                    'icon_ref':     self.layer['markers_canvas'].create_line(position,0, position, 15, fill='light goldenrod'),
                    }

            self.markers.append(temp)
            def sort(e):
                return e['frame']    
            
            self.markers.sort(key=sort)
            self.add_action("markers", self.markers)

        # elif action=='stop':
        #     if self.stop_marker == self.video_slider.get():
        #         self.stop_marker = []
        #         self.add_action('set_stop', -1)
        #         self.video_slider_canvas.delete(self.stop_image)
        #     else:
        #         self.video_slider_canvas.delete(self.stop_image)
        #         self.stop_marker = self.video_slider.self.timeline_position
        #         self.add_action('set_stop', self.stop_marker)
        #
        #         width = self.video_slider_canvas.winfo_width() - 30
        #         position = 15 + int(width * self.video_slider.self.timeline_position / self.video_slider.configure('to')[4])
        #         self.stop_image = self.video_slider_canvas.create_image(position, 30, image=self.stop_marker_icon)
         
        elif action=='delete':
            for i in range(len(self.markers)):
                if self.markers[i]['frame'] == self.video_slider.get():
                    self.layer['markers_canvas'].delete(self.markers[i]['icon_ref'])
                    self.markers.pop(i)
                    break
        
        elif action=='prev':
        
            temp=[]
            for i in range(len(self.markers)):
                temp.append(self.markers[i]['frame'])
            idx = bisect.bisect_left(temp, self.video_slider.get())
            
            if idx > 0:            
                self.video_slider.set(self.markers[idx-1]['frame'])

                self.add_action('get_requested_video_frame', self.markers[idx-1]['frame'])
                self.parameter_update_from_marker(self.markers[idx-1]['frame'])
                
        elif action=='next':        
            temp=[]
            for i in range(len(self.markers)):
                temp.append(self.markers[i]['frame'])
            idx = bisect.bisect(temp, self.video_slider.get())
            
            if idx < len(self.markers):
                self.video_slider.set(self.markers[idx]['frame'])

                self.add_action('get_requested_video_frame', self.markers[idx]['frame'])
                self.parameter_update_from_marker(self.markers[idx]['frame'])
        
        # resize canvas
        else :

            self.layer['markers_canvas'].delete('all')
            width = self.layer['markers_canvas'].winfo_width()-20-40-20
            
            for marker in self.markers:
                position = 20+int(width*marker['frame']/self.video_slider.get_length())
                marker['icon_ref'] = self.layer['markers_canvas'].create_line(position,0, position, 15, fill='light goldenrod')



                
    def toggle_stop(self):
        if self.stop_marker == self.video_slider.self.timeline_position:
            self.stop_marker = []
            self.add_action('set_stop', -1)
            self.video_slider_canvas.delete(self.stop_image)
        else:
            self.video_slider_canvas.delete(self.stop_image)
            self.stop_marker = self.video_slider.self.timeline_position
            self.add_action('set_stop', self.stop_marker)
        
            width = self.video_slider_canvas.winfo_width()-30
            position = 15+int(width*self.video_slider.self.timeline_position/self.video_slider.configure('to')[4])  
            self.stop_image = self.video_slider_canvas.create_image(position, 30, image=self.stop_marker_icon)

  
    def save_image(self):
        filename =  self.media_file_name[0]+"_"+str(time.time())[:10]
        filename = os.path.join(self.json_dict["saved videos"], filename)
        cv2.imwrite(filename+'.png', cv2.cvtColor(self.video_image, cv2.COLOR_BGR2RGB))
        print('Image saved as:', filename+'.png')
   
    def clear_mem(self):
        self.widget['RestorerSwitch'].set(False)
        self.widget['OccluderSwitch'].set(False)
        self.widget['FaceParserSwitch'].set(False)
        self.widget['CLIPSwitch'].set(False)
        self.widget['SwapFacesButton'].set(False)

        self.models.delete_models()
        torch.cuda.empty_cache()

        
        
# Refactor this, doesn't seem very efficient        
    def parameter_update_from_marker(self, frame):
    
        # sync marker data
        temp=[]
        # create a separate list with the list of frame numbers with markers
        for i in range(len(self.markers)):
            temp.append(self.markers[i]['frame'])
        # find the marker frame to the left of the current frame
        idx = bisect.bisect(temp, frame) 
        # update UI with current marker state data
        if idx>0:
            # update paramter dict with marker entry 
            self.parameters = copy.deepcopy(self.markers[idx-1]['parameters'])
  
            # Update ui
            for key, value in self.parameters.items():
                self.widget[key].set(self.parameters[key], request_frame=False)


            # self.CLIP_text.delete(0, tk.END)
            # self.CLIP_text.insert(0, self.parameters['CLIPText'])

    def toggle_audio(self):
        self.widget['AudioButton'].toggle_button()
        self.control['AudioButton'] = self.widget['AudioButton'].get()        
        self.add_action('control', self.control)
        
    def toggle_maskview(self):
        self.widget['MaskViewButton'].toggle_button()
        self.control['MaskViewButton'] = self.widget['MaskViewButton'].get()        
        self.add_action('control', self.control)
        self.add_action('get_requested_video_frame', self.video_slider.get())
        
    def parameter_io(self, task):
        if task=='save':
            with open("saved_parameters.json", "w") as save_file:
                json.dump(self.parameters, save_file)

        elif task=='load':
            try:
                load_file = open("saved_parameters.json", "r")
            except FileNotFoundError:
                print('No save file created yet!')
            else: 
                # Load the file and save it to parameters
                self.parameters = json.load(load_file)
                load_file.close()
                
                # Update the UI
                for key, value in self.parameters.items():
                    self.widget[key].set(value, request_frame=False)

            self.add_action('parameters', self.parameters)            
            self.add_action('control', self.control)
            self.add_action('get_requested_video_frame', self.video_slider.get())

        elif task=='default':
            # Update the UI
            for key, value in self.parameters.items():
                self.widget[key].load_default()

            self.add_action('parameters', self.parameters)            
            self.add_action('control', self.control)
            self.add_action('get_requested_video_frame', self.video_slider.get())



    def findCosineDistance2(self, vector1, vector2):
        cos_dist = 1.0 - np.dot(vector1, vector2)/(np.linalg.norm(vector1)*np.linalg.norm(vector2)) # 2..0

        print(np.dot(vector1, vector2))

        return cos_dist