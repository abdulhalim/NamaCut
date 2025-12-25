# --------------------------------------------------
# Video transformation management
# --------------------------------------------------
class VideoTransformer:
    def __init__(self):
        self.current_rotation = 0
        self.flip_horizontal = False
        self.flip_vertical = False
        self.crop_rect = None
        self.crop_mode = False
        
    # --------------------------------------------------
    # Rotation and flip operations
    # --------------------------------------------------
    def rotate_video(self, rotation_type):
        if rotation_type == "left": 
            self.current_rotation = (self.current_rotation - 90) % 360
        elif rotation_type == "right": 
            self.current_rotation = (self.current_rotation + 90) % 360
        elif rotation_type == "horizontal": 
            self.flip_horizontal = not self.flip_horizontal
        elif rotation_type == "vertical": 
            self.flip_vertical = not self.flip_vertical
        elif rotation_type == "reset":
            self.current_rotation = 0
            self.flip_horizontal = False
            self.flip_vertical = False
            self.crop_rect = None
            self.crop_mode = False
            
    # --------------------------------------------------
    # UI synchronization
    # --------------------------------------------------
    def sync_with_player(self, media_player):
        if hasattr(media_player, 'current_rotation'):
            self.current_rotation = media_player.current_rotation
            self.flip_horizontal = media_player.flip_horizontal
            self.flip_vertical = media_player.flip_vertical
            self.crop_mode = media_player.crop_mode
            
            if self.crop_mode and hasattr(media_player, 'get_current_crop_rect'):
                current_crop = media_player.get_current_crop_rect()
                if current_crop:
                    self.crop_rect = current_crop
                else:
                    self.crop_rect = media_player.crop_rect
            else:
                self.crop_rect = media_player.crop_rect
            
    def sync_with_widget(self, video_player):
        if hasattr(video_player, 'current_rotation'):
            self.current_rotation = video_player.current_rotation
            self.flip_horizontal = video_player.flip_horizontal
            self.flip_vertical = video_player.flip_vertical
    
    # --------------------------------------------------
    # FFmpeg filter generation
    # --------------------------------------------------
    def build_video_filter_for_ffmpeg(self):
        parts = []
        
        if self.crop_rect and self.crop_mode:
            x, y, w, h = self.crop_rect
            parts.append(f"crop={w}:{h}:{x}:{y}")

        if self.current_rotation == 90:
            parts.append("transpose=1")
        elif self.current_rotation == 180:
            parts.append("transpose=1,transpose=1")
        elif self.current_rotation == 270:
            parts.append("transpose=2")

        if self.flip_horizontal: 
            parts.append("hflip")
        if self.flip_vertical: 
            parts.append("vflip")

        if not parts: 
            return None
            
        return ",".join(parts)
        
    # --------------------------------------------------
    # Crop operations
    # --------------------------------------------------
    def set_crop_rect(self, x, y, width, height):
        self.crop_rect = [x, y, width, height]
        
    def toggle_crop_mode(self):
        self.crop_mode = not self.crop_mode
        return self.crop_mode
        
    # --------------------------------------------------
    # Information methods
    # --------------------------------------------------
    def get_transformation_info(self):
        info = []
        if self.current_rotation != 0:
            info.append(f"Rotation: {self.current_rotation}°")
        if self.flip_horizontal:
            info.append("Flip: Horizontal")
        if self.flip_vertical:
            info.append("Flip: Vertical")
        if self.crop_mode and self.crop_rect:
            x, y, w, h = self.crop_rect
            info.append(f"Crop: {w}x{h}")
        return ", ".join(info) if info else "No transformations"