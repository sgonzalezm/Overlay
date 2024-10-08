import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import os
import time

STOCK_FOLDER = 'C:/video_stock/'

# Función para guardar la imagen capturada
def guardar_foto(frame):
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"captura_{timestamp}.jpg"
    cv2.imwrite(filename, frame)
    print(f"Imagen guardada como {filename}")

# Función de captura al presionar el botón
def capturar():
    global resultado
    if resultado is not None:
        guardar_foto(resultado)

# Función para mostrar el frame en la ventana de Tkinter
def mostrar_frame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)
    imgtk = ImageTk.PhotoImage(image=img)
    video_label.imgtk = imgtk
    video_label.config(image=imgtk)

# Función para manejar la selección del video y proceder al empalme
def seleccionar_video():
    global video_seleccionado
    seleccion = lista_videos.curselection()
    if seleccion:
        video_seleccionado = lista_videos.get(seleccion)
        print(f"Video seleccionado: {video_seleccionado}")
        ventana_seleccion.withdraw()
        iniciar_empalme()

# Ventana de selección de video
def ventana_seleccion_videos():
    global lista_videos, ventana_seleccion

    ventana_seleccion = tk.Tk()
    ventana_seleccion.title("Seleccionar Video de Stock")

    label = tk.Label(ventana_seleccion, text="Selecciona un video de stock:")
    label.pack()

    lista_videos = tk.Listbox(ventana_seleccion)
    lista_videos.pack()

    videos = os.listdir(STOCK_FOLDER)
    for video in videos:
        lista_videos.insert(tk.END, video)

    button = tk.Button(ventana_seleccion, text="Seleccionar", command=seleccionar_video)
    button.pack()

    ventana_seleccion.mainloop()

# Función para iniciar el empalme con el video seleccionado
def iniciar_empalme():
    global resultado, cap, personaje, video_label, ventana_empalme

    ventana_empalme = tk.Toplevel()
    ventana_empalme.title("Superposición de video y cámara")

    video_label = tk.Label(ventana_empalme)
    video_label.pack()

    button = tk.Button(ventana_empalme, text="Capturar foto", command=capturar)
    button.pack()

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara.")
        return

    video_path = os.path.join(STOCK_FOLDER, video_seleccionado)
    personaje = cv2.VideoCapture(video_path)

    if not personaje.isOpened():
        print("Error: No se pudo cargar el video del personaje.")
        return

    resultado = None

    def actualizar_video():
        global resultado
        ret, frame = cap.read()
        if not ret:
            print("Error al leer el frame de la cámara.")
            ventana_empalme.after(10, actualizar_video)
            return

        ret_personaje, frame_personaje = personaje.read()
        if not ret_personaje:
            personaje.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_personaje, frame_personaje = personaje.read()

        if frame_personaje is None:
            print("Error: No se pudo leer el frame del personaje.")
            ventana_empalme.after(10, actualizar_video)
            return

        frame_personaje = cv2.resize(frame_personaje, (frame.shape[1], frame.shape[0]))

        hsv_personaje = cv2.cvtColor(frame_personaje, cv2.COLOR_BGR2HSV)

        # Ajuste de los valores del verde (más amplio para asegurar buena detección)
        lower_green = np.array([35, 68, 68])
        upper_green = np.array([85, 255, 255])

        # Crear la máscara para el color verde
        mask = cv2.inRange(hsv_personaje, lower_green, upper_green)

        # Aplicar erosión y dilatación para limpiar la máscara
        kernel = np.ones((3, 3), np.uint8)
        mask = cv2.erode(mask, kernel, iterations=1)
        mask = cv2.dilate(mask, kernel, iterations=1)

        # Invertir la máscara para obtener la parte del personaje sin fondo verde
        mask_inv = cv2.bitwise_not(mask)

        # Separar el personaje del fondo verde
        personaje_sin_fondo = cv2.bitwise_and(frame_personaje, frame_personaje, mask=mask_inv)

        # Técnica de "despillage": eliminar restos verdes suavizando y desaturando
        hls = cv2.cvtColor(personaje_sin_fondo, cv2.COLOR_BGR2HLS)
        hls[:, :, 2] = np.where(mask == 0, hls[:, :, 2] * 0.5, hls[:, :, 2])  # Reducir brillo en áreas verdes
        hls[:, :, 1] = np.where(mask == 0, hls[:, :, 1] * 0.7, hls[:, :, 1])  # Reducir la luminancia para minimizar spill
        personaje_sin_fondo = cv2.cvtColor(hls, cv2.COLOR_HLS2BGR)

        # Extraer el fondo de la cámara en las áreas donde el personaje no está
        fondo_camara = cv2.bitwise_and(frame, frame, mask=mask)

        # Combinar el fondo de la cámara con el personaje
        resultado = cv2.add(fondo_camara, personaje_sin_fondo)

        # Mostrar el resultado final en la ventana de Tkinter
        mostrar_frame(resultado)

        ventana_empalme.after(10, actualizar_video)

    ventana_empalme.after(10, actualizar_video)
    ventana_empalme.mainloop()

    cap.release()
    personaje.release()

ventana_seleccion_videos()
