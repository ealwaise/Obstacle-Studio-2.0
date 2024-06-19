import os
from PyQt6.QtWidgets import (QWidget,
                             QGraphicsItem,
                             QGraphicsItemGroup,
                             QGraphicsRectItem,
                             QGraphicsPixmapItem,
                             QStyleOptionGraphicsItem)
from PyQt6.QtGui import (QColor,
                         QPixmap,
                         QPainter,
                         QPen)
from PyQt6.QtCore import (QPointF,
                          QRectF,
                          QVariant)
from src import sc_data
from src import read_write

class Grid(QGraphicsItem):
    """A graphics item consisting of grid lines."""
    grid_color = QColor(150, 150, 150, 75)
    # We draw the grid lines at points which are not multiples of 32 with a lighter color to more
    # easily distinguish the 1x1 tiles.
    subgrid_color = QColor(150, 150, 150, 25)

    def __init__(self, width: int, height: int, size: list[int], subgrid=False):
        super().__init__()
        
        self.width, self.height = width, height
        self.size = size
        self.subgrid = subgrid
        color = QColor()
        if subgrid:
            color.setRgba(Grid.subgrid_color.rgba())
        else:
            color.setRgba(Grid.grid_color.rgba())
        self.pen = QPen(color)
        self.pen.setWidth(0)
        
    def boundingRect(self) -> QRectF:
        """Returns the bounding rectangle of the grid, which is the size of the entire scene."""
        return QRectF(0, 0, self.width, self.height)

    def paint(self,
              painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget=None) -> None:
        """Draws the grid lines."""
        painter.setPen(self.pen)
        for x in range(0, self.width, self.size):
            if x % 32 != 0 or not self.subgrid:
                painter.drawLine(x, 0, x, self.height - 1)
        for y in range(0, self.height, self.size):
            if y % 32 != 0 or not self.subgrid:
                painter.drawLine(0, y, self.width - 1, y)
        
class GridSnappingItemGroup(QGraphicsItemGroup):
    """A QGraphicsItemGroup which snaps to the grid."""

    def __init__(self):
        super().__init__()
        
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: QVariant) -> None:
        """Snaps the group to the grid."""
        scene = self.scene()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and scene:
            rect = self.boundingRect()
            x, y = scene.snap_to_grid(value.x(),
                                      value.y(),
                                      scene.grid_size,
                                      rect.width() / 32, rect.height() / 32)
            return QPointF(x, y)
        return super().itemChange(change, value)
        
class BrushHighlight(QGraphicsItemGroup):
    """A transparent graphics item used to highlight where items will be placed."""
    color = QColor(225, 255, 225)
    opacity = 0.3
    
    def __init__(self, shape: list[list[int]], width: float, height: float):
        super().__init__()
        
        self.setOpacity(self.opacity)
        self.change_geometry(shape, width, height)
        self.draw()
        
    def boundingRect(self) -> QRectF:
        """Returns the bounding rectangle of the brush."""
        return self.childrenBoundingRect()
    
    def change_geometry(self, shape: list[list[int]], width: float, height: float) -> None:
        """Changes the brush's geometry based upon the input parameters."""
        self.shape = shape
        self.width, self.height = width, height
        self.total_width, self.total_height = width*len(shape), height*len(shape[0])
        self.draw()
        
    def draw(self) -> None:
        """Adds the rectangles based on the shape, width, and height."""
        for item in self.childItems():
            self.removeFromGroup(item)
        for i in range(len(self.shape)):
            for j in range(len(self.shape[0])):
                if not self.shape[i][j]:
                    continue
                rect = QGraphicsRectItem(0, 0, 32*self.width, 32*self.height)
                rect.setBrush(self.color)
                self.addToGroup(rect)
                rect.setPos(32*j*self.width, 32*i*self.height)

class TerrainTile(QGraphicsPixmapItem):
    """A graphics item depicting a terrain tile image and storing the tile index."""

    def __init__(self, num: int, pixmap: QPixmap):
        super().__init__(pixmap)
        self.num = num
        
class Location(QGraphicsItem):
    """A graphics item which mimics the functions of a Starcraft location."""
    prefix = ""
    convention = read_write.read_setting("Location numbering convention")
    interior_color = QColor(0, 110, 200, 75)
    interior_color_highlight = QColor(0, 255, 0, 75)
    border_color = QColor(0, 255, 0, 255)
    text_color = QColor(255, 255, 255, 255)
    pixel_tolerance = 8
    ID_offset = 0
    
    @classmethod
    def set_ID_offset(self, offset: int) -> None:
        """Sets the ID_offset to offset."""
        Location.ID_offset = offset
    
    @classmethod
    def set_prefix(self, prefix: str) -> None:
        """Sets the location prefix to prefix."""
        Location.prefix = prefix
    
    @classmethod
    def set_numbering_convention(self, index: int) -> None:
        """Sets the location numbering convention to index."""
        Location.convention = index

    def __init__(self, width: float, height: float, num: int, ID: int):
        super().__init__()

        self.width, self.height = width, height
        self.num = num
        self.ID = ID + Location.ID_offset
        self.name = self.format_name(0)
        self.color = QColor()
        self.color.setRgba(Location.interior_color_highlight.rgba())
        
    def boundingRect(self):
        """Returns the bounding rectangle of the location."""
        return QRectF(0, 0, 32*self.width, 32*self.height)

    def paint(self,
              painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget=None) -> None:
        """Paints the blue location overlay, the border, and the label text."""
        painter.fillRect(1, 1, int(32*self.width) - 2, int(32*self.height) - 2, self.color)
        
        pen = QPen(Location.border_color)
        pen.setWidth(0)
        painter.setPen(pen)
        painter.drawRect(0, 0, int(32*self.width) - 1, int(32*self.height) - 1)
        
        pen = QPen(Location.text_color)
        painter.setPen(pen)
        painter.drawText(4, 1, int(32*self.width) - 8, int(32*self.height) - 2, 1, self.name)
        
    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: QVariant) -> None:
        """Snaps the location to the grid."""
        scene = self.scene()
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and scene:
            x, y = scene.snap_to_grid(value.x(), value.y(), scene.grid_size, self.width, self.height)
            return QPointF(x, y)
        return super().itemChange(change, value)
        
    def center(self) -> float:
        """Returns the center of the location."""
        return self.boundingRect().center()
        
    def x(self) -> int:
        """Returns the x coordinate of the top-left corner of the location."""
        return int(self.pos().x())
    
    def y(self) -> int:
        """Returns the y coordinate of the top-left corner of the location."""
        return int(self.pos().y())
        
    def set_visibility(self, visible: bool) -> None:
        """Makes the location visible if visible is true and invisible otherwise."""
        self.setVisible(visible)
        
    def set_movable(self, movable: bool) -> None:
        """Changes whether or not the location can be moved."""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, movable)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, movable)
        
    def in_moving_layer_group(self, motion: bool) -> None:
        """If motion is true, highlights this location and add its to a moveable item group.
        If motion is false, unhighlights this location and removes it from a moveable item group.
        """
        if motion:
            self.set_color(self.interior_color_highlight)
        else:
            self.set_color(self.interior_color)
        self.scene().adjust_moving_layer_group(self, motion)
        
    def format_name(self, num_zeros: int) -> str:
        """Determines the correct name for the location and returns it."""
        prefix = Location.prefix
        suffix = None

        if Location.convention == 0:
            suffix = str(self.num)
        elif Location.convention == 1:
            suffix = '0'*(num_zeros) + str(self.num)
        elif Location.convention == 2:
            suffix = chr(97 + (self.num - 1) % 26)
            if self.num > 26:
                suffix = chr(96 + (self.num - 1) // 26) + suffix
        elif Location.convention == 3:
            suffix = chr(65 + (self.num - 1) % 26)
            if self.num > 26:
                suffix = chr(64 + (self.num - 1) // 26) + suffix
            
        return prefix + suffix
    
    def update_data(self, num_locs: int) -> None:
        """Updates the location's name and ID."""
        num_zeros = len(str(num_locs)) - len(str(self.num))
        self.name = self.format_name(num_zeros)
        self.ID = self.num + self.ID_offset
        self.update()
        
    def set_color(self, color: QColor) -> None:
        """Sets the color of the location interior to color."""
        self.color.setRgba(color.rgba())
        self.update()

    def resize(self,
               old_center: QPointF,
               x: int,
               y: int,
               width: float,
               height: float) -> QPointF:
        """Resizes the location to width x height and changes its top-left corner to (x, y).
        Returns the amount by which to shift child items.
        """
        self.prepareGeometryChange()
        self.width, self.height = width, height
        
        # We have to reposition event images to keep them centered on the location. The return
        # value is used to update the positions of obstacle events.
        shift = self.center() - old_center
        for child in self.childItems():
            child.moveBy(shift.x(), shift.y())
        return shift

class EventImage(QGraphicsPixmapItem):
    """A graphical item storing an image and its ID."""

    def __init__(self,
                 event_type: str,
                 count: int,
                 ID: int,
                 pixmap:
                 QPixmap,
                 teleport_cell: list[int]=[-1, -1],
                 teleport_player: int=-1):
        super().__init__(pixmap)
        
        self.event_type = event_type
        self.ID = ID
        self.count = count
        self.width, self.height = pixmap.width(), pixmap.height()
        self.teleport_cell = teleport_cell
        self.teleport_player = teleport_player
        
    def boundingRect(self) -> None:
        """Returns the bounding rectangle of the location."""
        # We center the bounding rectangle at (0, 0) for centering of images on locations.
        return QRectF(-self.width / 2, -self.height / 2, self.width, self.height)
        
    def paint(self,
              painter: QPainter,
              option: QStyleOptionGraphicsItem,
              widget: QWidget=None) -> None:
        """Paints the image."""
        painter.translate(-self.width / 2, -self.height / 2)
        QGraphicsPixmapItem.paint(self, painter, option, widget)