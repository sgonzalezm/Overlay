import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import os
import time

STOCK_FOLDER = 'C:/Users/diego/Desktop/Video Overlay/video_stock/'

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
    # Convertir de BGR a RGB para Pillow
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = Image.fromarray(frame)  # Convertir a imagen de Pillow
    imgtk = ImageTk.PhotoImage(image=img)  # Convertir la imagen a formato de Tkinter

    # Mantener la referencia en la etiqueta del video
    video_label.imgtk = imgtk  # Guardar la referencia en el widget de video
    video_label.config(image=imgtk)  # Actualizar el widget con la nueva imagen

# Función para manejar la selección del video y proceder al empalme
def seleccionar_video():
    global video_seleccionado
    seleccion = lista_videos.curselection()
    if seleccion:
        video_seleccionado = lista_videos.get(seleccion)
        print(f"Video seleccionado: {video_seleccionado}")
        ventana_seleccion.withdraw()  # Ocultar ventana de selección
        iniciar_empalme()  # Llamar al empalme

# Ventana de selección de video
def ventana_seleccion_videos():
    global lista_videos, ventana_seleccion

    ventana_seleccion = tk.Tk()
    ventana_seleccion.title("Seleccionar Video de Stock")

    label = tk.Label(ventana_seleccion, text="Selecciona un video de stock:")
    label.pack()

    lista_videos = tk.Listbox(ventana_seleccion)
    lista_videos.pack()

    # Cargar los videos de la carpeta
    videos = os.listdir(STOCK_FOLDER)
    for video in videos:
        lista_videos.insert(tk.END, video)

    button = tk.Button(ventana_seleccion, text="Seleccionar", command=seleccionar_video)
    button.pack()

    ventana_seleccion.mainloop()

# Función para iniciar el empalme con el video seleccionado
def iniciar_empalme():
    global resultado, cap, personaje, video_label, ventana_empalme

    # Ventana para la superposición de videos
    ventana_empalme = tk.Toplevel()  # Crear una nueva ventana en lugar de Tk
    ventana_empalme.title("Superposición de video y cámara")

    video_label = tk.Label(ventana_empalme)
    video_label.pack()

    button = tk.Button(ventana_empalme, text="Capturar foto", command=capturar)
    button.pack()

    # Captura de video en tiempo real de la cámara
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara.")
        return

    # Cargar el video del personaje (video seleccionado de stock)
    video_path = os.path.join(STOCK_FOLDER, video_seleccionado)
    personaje = cv2.VideoCapture(video_path)

    if not personaje.isOpened():
        print("Error: No se pudo cargar el video del personaje.")
        return

    resultado = None  # Para almacenar el frame actual para la captura

    def actualizar_video():
        global resultado
        # Leer el frame de la cámara
        ret, frame = cap.read()

        if not ret:
            print("Error al leer el frame de la cámara.")
            ventana_empalme.after(10, actualizar_video)
            return

        # Leer el frame del video del personaje
        ret_personaje, frame_personaje = personaje.read()

        if not ret_personaje:
            # Reiniciar el video del personaje si llega al final
            personaje.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret_personaje, frame_personaje = personaje.read()

        if frame_personaje is None:
            print("Error: No se pudo leer el frame del personaje.")
            ventana_empalme.after(10, actualizar_video)
            return

        # Redimensionar el frame del personaje al tamaño del frame de la cámara
        frame_personaje = cv2.resize(frame_personaje, (frame.shape[1], frame.shape[0]))

        # Convertir el frame del personaje a HSV
        hsv_personaje = cv2.cvtColor(frame_personaje, cv2.COLOR_BGR2HSV)

        # Definir el rango de color verde en HSV
        lower_green = np.array([35, 100, 100])
        upper_green = np.array([85, 255, 255])

        # Crear una máscara para el color verde
        mask = cv2.inRange(hsv_personaje, lower_green, upper_green)

        # Invertir la máscara para obtener el personaje sin el fondo verde
        mask_inv = cv2.bitwise_not(mask)

        # Extraer el personaje sin fondo
        personaje_sin_fondo = cv2.bitwise_and(frame_personaje, frame_personaje, mask=mask_inv)

        # Extraer el fondo de la imagen de la cámara donde estará el personaje
        fondo_camara = cv2.bitwise_and(frame, frame, mask=mask)

        # Combinar el personaje con la imagen de la cámara
        resultado = cv2.add(fondo_camara, personaje_sin_fondo)

        # Mostrar el frame en la ventana de Tkinter
        mostrar_frame(resultado)

        # Llamar a la función otra vez después de 10 ms
        ventana_empalme.after(10, actualizar_video)

    # Iniciar la actualización del video
    ventana_empalme.after(10, actualizar_video)

    # Ejecutar la ventana de superposición
    ventana_empalme.mainloop()

    # Liberar la cámara y los videos al final
    cap.release()
    personaje.release()

# Iniciar la ventana de selección de videos
ventana_seleccion_videos()

