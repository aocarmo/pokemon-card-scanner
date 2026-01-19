import cv2
import numpy as np
from typing import Optional, Tuple

class CardDetector:
    """Detecta e extrai carta da imagem"""
    
    def find_card_contour_raw(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """Retorna contorno da carta sem processar"""
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return None
        
        return self._find_card_contour(img)
    
    def detect_and_crop(self, image_bytes: bytes) -> Optional[bytes]:
        """Detecta carta e retorna imagem cortada"""
        
        # Decode image
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return image_bytes
        
        # Find card contour
        contour = self._find_card_contour(img)
        
        if contour is None:
            return image_bytes
        
        # Crop and transform
        cropped = self._crop_card(img, contour)
        
        # Encode back to bytes
        _, buffer = cv2.imencode('.jpg', cropped)
        return buffer.tobytes()
    
    def _find_card_contour(self, img: np.ndarray) -> Optional[np.ndarray]:
        """Encontra contorno da carta"""
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return None
        
        # Find largest rectangular contour
        for contour in sorted(contours, key=cv2.contourArea, reverse=True):
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            
            if len(approx) == 4:
                area = cv2.contourArea(approx)
                img_area = img.shape[0] * img.shape[1]
                
                if area > img_area * 0.1:
                    return approx
        
        return None
    
    def _crop_card(self, img: np.ndarray, contour: np.ndarray) -> np.ndarray:
        """Corta e aplica transformação de perspectiva"""
        
        pts = contour.reshape(4, 2).astype(np.float32)
        rect = self._order_points(pts)
        
        # Card ratio 2.5:3.5
        width = 500
        height = int(width * 3.5 / 2.5)
        
        dst = np.array([
            [0, 0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0, height - 1]
        ], dtype=np.float32)
        
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (width, height))
        
        return warped
    
    def _order_points(self, pts: np.ndarray) -> np.ndarray:
        """Ordena pontos: top-left, top-right, bottom-right, bottom-left"""
        
        sorted_pts = pts[np.argsort(pts[:, 1])]
        
        top = sorted_pts[:2]
        top = top[np.argsort(top[:, 0])]
        
        bottom = sorted_pts[2:]
        bottom = bottom[np.argsort(bottom[:, 0])]
        
        return np.array([top[0], top[1], bottom[1], bottom[0]], dtype=np.float32)
