from __future__ import annotations

import threading
import time
from typing import Iterator, TypedDict

import cv2
from flask import Flask, Response, jsonify, render_template, request


aplicacion = Flask(__name__)

LIMITE_CAMARAS = 10
CALIDAD_JPEG = 85
PUERTO = 5000
BIND_ADDRESS = '127.0.0.1'


class InformacionCamara(TypedDict):
    indice: int
    nombre: str


class GestorDeCamaras:
  def __init__(self) -> None:
    self._captura: cv2.VideoCapture | None = None
    self._indice: int | None = None
    self._bloqueo = threading.Lock()

  def camaras_disponibles(self, limite: int = LIMITE_CAMARAS) -> list[InformacionCamara]:
    camaras: list[InformacionCamara] = []
    for indice_camara in range(limite):
      captura = cv2.VideoCapture(indice_camara, cv2.CAP_DSHOW)
      if captura.isOpened():
        camaras.append({"indice": indice_camara, "nombre": f"Cámara {indice_camara + 1}"})
      captura.release()
    return camaras

  def seleccionar(self, indice_camara: int) -> bool:
    nueva_captura = cv2.VideoCapture(indice_camara, cv2.CAP_DSHOW)
    if not nueva_captura.isOpened():
      nueva_captura.release()
      return False
    with self._bloqueo:
      if self._captura is not None:
        self._captura.release()
      self._captura = nueva_captura
      self._indice = indice_camara
    return True

  def transmitir_frames(self) -> Iterator[bytes]:
    while True:
      with self._bloqueo:
        captura = self._captura
      if captura is None:
        time.sleep(0.1)
        continue
      lectura_correcta, fotograma = captura.read()
      if not lectura_correcta:
        time.sleep(0.1)
        continue
      codificacion_correcta, fotograma_codificado = cv2.imencode(
        '.jpg', fotograma, [cv2.IMWRITE_JPEG_QUALITY, CALIDAD_JPEG]
      )
      if codificacion_correcta:
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + fotograma_codificado.tobytes() + b'\r\n')

  @property
  def indice(self) -> int | None:
    return self._indice


gestor_camaras = GestorDeCamaras()


@aplicacion.get('/')
def pagina_principal() -> str:
  return render_template('index.html')


@aplicacion.get('/api/cameras')
def listar_camaras() -> Response:
  return jsonify(gestor_camaras.camaras_disponibles())


@aplicacion.post('/api/select')
def seleccionar_camara() -> Response:
  datos_recibidos = request.get_json(silent=True) or {}
  try:
    indice_camara = int(datos_recibidos['indice'])
  except (KeyError, TypeError, ValueError):
    return jsonify(error='Índice de cámara inválido.'), 400
  if not 0 <= indice_camara < LIMITE_CAMARAS or not gestor_camaras.seleccionar(indice_camara):
    return jsonify(error='No se pudo abrir esa cámara.'), 404
  return jsonify(indice=indice_camara, nombre=f'Cámara {indice_camara + 1}')


@aplicacion.get('/video_feed')
def transmision_video() -> Response:
  return Response(gestor_camaras.transmitir_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


if __name__ == '__main__':
  aplicacion.run(host=BIND_ADDRESS, port=PUERTO, threaded=True, debug=False)