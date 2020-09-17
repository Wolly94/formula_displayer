from tkinter import *
import tkinter.font

from basics import *
from dataclasses import dataclass

def_pixel_height = 100

root = Tk()

UnscaledFont = tkinter.font.Font(family = "arial", size = -def_pixel_height)

class Size:
    def __init__(self, w, h):
        self.width = w
        self.height = h

    def __str__(self):
        return "width: "+str(self.width)+" height: "+str(self.height)

class Position:
    def __init__(self, xoff, yoff, yoff_rel): #yoff is offset to ycenter
        self.xoff = xoff
        self.yoff = yoff
        self.yoff_rel = yoff_rel

    def __str__(self):
        return "xoff: "+str(self.xoff)+" yoff: "+str(self.yoff)+" relative yoff: "+str(self.yoff_rel)

def get_text_size(text):
    font = UnscaledFont
    return font.measure(text), font.metrics("linespace")

plus_width = get_text_size("+")[0]
dot_width = get_text_size("*")[0]

def str_to_term(s: str):
    t1, c, t2 = split(s)
    if (c == None) and (t2 == None):
        return SingleTerm(t1)
    elif t2 == None:
        return BraceTerm(str_to_term(remove_braces(t1)))
    elif c == "+":
        s = str_to_term(t1)
        if not isinstance(s, SumTerm):
            s = SumTerm([s])
        return s + str_to_term(t2)
    elif c == "-":
        if len(t1) == 0:
            t = str_to_term(t2)
            if isinstance(t, SignedTerm):
                return t
            else:
                return SignedTerm(t)
        else:
            return SumTerm([str_to_term(t1)]) - str_to_term(t2)
    elif c == "*":
        return ProdTerm([str_to_term(t1)]) * str_to_term(t2)
    elif c == "/":
        return DivTerm(str_to_term(remove_braces(t1)), str_to_term(remove_braces(t2)))
    elif c == "^":
        return ExpTerm(str_to_term(t1), str_to_term(remove_braces(t2)))
    else:
        print("Not covered!!!")
        return Term;


class Term:
    def __init__(self):
        self.size = None
        self.pos = None
        self.bbox = None
        self.id = None

    def get_bbox(self):
        return (self.pos.xoff, self.pos.yoff-self.pos.yoff_rel, self.pos.xoff + self.size.width, self.pos.yoff-self.pos.yoff_rel+self.size.height)

    def set_id(self, id):
        self.id = id

    def set_bbox(self, x0, y0, x1, y1):
        self.bbox = (x0, y0, x1, y1)

    def is_contained(self, a0, b0, a1, b1):
        (x0, y0, x1, y1) = self.bbox
        return (a0 <= x0) and (x1 <= a1) and (b0 <= y0) and (y1 <= b1)

    def contains(self, x, y):
        (x0, y0, x1, y1) = self.get_bbox()
        return (x0 <= x <= x1) and (y0 <= y <= y1)

    def contains_region(self, a0, b0, a1, b1):
        return self.contains(a0, b0) and self.contains(a0, b1) and self.contains(a1, b0) and self.contains(a1, b1)

    def overlaps(self, a0, b0, a1, b1):
        return self.contains(a0, b0) or self.contains(a0, b1) or self.contains(a1, b0) or self.contains(a1, b1)

    def contains_term(self, t):
        return self.get_parent(t) != None

    def get_lowest_container(self, x, y):
        pass

    def get_smallest_container(self, x0, y0, x1, y1):
        pass

    def get_parent(self, term):
        pass


class SingleTerm(Term):
    def __init__(self, s):
        super().__init__()
        self.content = s

    def render(self, xoff = 0, yoff = 0, scaled = False):
        (w, h) = get_text_size(self.content)
        if scaled:
            scale = ExpTerm.scale_factor
        else:
            scale = 1
        yoff_rel = h/2*scale
        self.size = Size(w*scale, h*scale)
        self.pos = Position(xoff, yoff, yoff_rel)

    def get_lowest_container(self, x, y):
        if self.contains(x, y):
            return self
        else:
            return None

    def get_smallest_container(self, x0, y0, x1, y1):
        if self.contains_region(x0, y0, x1, y1):
            return self, None
        else:
            return None, None

    def __str__(self):
        return "Single: "+self.content

    def get_parent(self, term):
        return None


class MonoTerm(Term):
    def __init__(self, t):
        super().__init__()
        self.t = t

    def get_lowest_container(self, x, y):
        if self.t.contains(x, y):
            return self.t.get_lowest_container(x, y)
        else:
            return self

    def get_smallest_container(self, x0, y0, x1, y1):
        if bbox_contains_bbox(self.get_bbox(), (x0, y0, x1, y1)):
            if self.t.contains_region(x0, y0, x1, y1):
                return self.t.get_smallest_container(x0, y0, x1, y1)
            else:
                return self, None
        else:
            return None, None

    def get_parent(self, term):
        if self.t == term:
            return self
        else:
            return self.t.get_parent(term)


class BraceTerm(MonoTerm):
    op_width = get_text_size("(")[0]
    def __init__(self, t):
        super().__init__(t)
        self.t = t

    def render(self, xoff = 0, yoff = 0, scaled = False):
        if scaled:
            scale = ExpTerm.scale_factor
        else:
            scale = 1
        self.t.render(xoff+scale*BraceTerm.op_width, yoff, scaled)
        self.size = Size(2*BraceTerm.op_width*scale + self.t.size.width, self.t.size.height)
        yoff_rel = self.t.pos.yoff_rel
        self.pos = Position(xoff, yoff, yoff_rel)

    def __str__(self):
        return "("+str(self.t)+")"


class SignedTerm(MonoTerm):
    op_width = plus_width # this must be the same!!!
    def __init__(self, t): # t is not allowed to be of type SignedTerm
        super().__init__(t)

    def render(self, xoff = 0, yoff = 0, scaled = False):
        if scaled:
            scale = ExpTerm.scale_factor
        else:
            scale = 1
        self.t.render(xoff+scale*SignedTerm.op_width, yoff, scaled)
        self.size = Size(SignedTerm.op_width*scale + self.t.size.width, self.t.size.height)
        yoff_rel = self.t.pos.yoff_rel
        self.pos = Position(xoff, yoff, yoff_rel)

    def __str__(self):
        return "-" + str(self.t)


class ListTerm(Term):
    def __init__(self, l):
        super().__init__()
        self.l = l

    def get_op_width(self):
        pass

    def render(self, xoff = 0, yoff = 0, scaled = False):
        if scaled:
            scale = ExpTerm.scale_factor
        else:
            scale = 1
        w = xoff
        h = 0
        yoff_rel = 0
        for (i, t) in enumerate(self.l):
            if (i != 0) and ((isinstance(self, SumTerm) and not isinstance(t, SignedTerm)) or isinstance(self, ProdTerm)):
                w += scale * self.get_op_width()
            t.render(w, yoff, scaled)
            w += t.size.width
            yoff_rel = max(yoff_rel, t.pos.yoff_rel)
            h = max(h, yoff_rel + t.size.height-t.pos.yoff_rel)
        self.size = Size(w-xoff, h)
        self.pos = Position(xoff, yoff, yoff_rel)

    def get_lowest_container(self, x, y):
        for t in self.l:
            if t.contains(x, y):
                return t.get_lowest_container(x, y)
        return self

    def get_smallest_container(self, x0, y0, x1, y1):
        bbox = self.get_bbox()
        if y0 >= bbox[3] or y1 <= bbox[1]:
            return None, None
        i0 = 0
        j0 = len(self.l)-1
        while i0 < len(self.l) and self.l[i0].get_bbox()[0] < x0:
            i0 += 1
        while j0 >= 0 and self.l[j0].get_bbox()[2] > x1:
            j0 -= 1
        i0 = max(0, i0-1)
        j0 = min(len(self.l)-1, j0+1)
        if i0 == j0:
            if self.l[i0].contains_region(x0, y0, x1, y1):
                v = self.l[i0].get_smallest_container(x0, y0, x1, y1)
                if v != self.l[i0]:
                    return v
                else:
                    return self, (i0, j0+1)
            else:
                return self.l[i0], None
        elif (i0 != 0) or (j0 != len(self.l)-1):
            return self, (i0, j0+1)
        else:
            return self, None

    def get_parent(self, term):
        for t in self.l:
            if t == term:
               return self
            else:
                r = t.get_parent(term)
                if r != None:
                    return r
        return None


class SumTerm(ListTerm):
    op_width = plus_width
    def __init__(self, l):
        super().__init__(l)

    def __add__(self, other: Term):
        if isinstance(other, SumTerm):
            self.l += other.l
        else:
            #if isinstance(other, SignedTerm) and ((isinstance(other.t, SignedTerm)) or isinstance(other.t, SumTerm))):
            #    other = BraceTerm(other)
            #self.l += [other]
            if isinstance(other, SignedTerm) and (isinstance(other.t, SignedTerm) or isinstance(other.t, SumTerm)):
                other = BraceTerm(other)
            self.l += [other]
        return self

    def __sub__(self, other: Term):
        if isinstance(other, SignedTerm):
            other = BraceTerm(other) # or change it to yield --=+
        self.l += [SignedTerm(other)]
        return self

    def get_op_width(self):
        return SumTerm.op_width

    def __str__(self):
        r = "SumTerm: " + str(self.l[0])
        for t in self.l[1:]:
            r += " + "+str(t)
        return r


class ProdTerm(ListTerm):
    op_width = dot_width
    def __init__(self, l):
        super().__init__(l)

    def __mul__(self, other: Term):
        if isinstance(other, ProdTerm):
            self.l += other.l
        else:
            if isinstance(other, SumTerm) or isinstance(other, SignedTerm):
                other = BraceTerm(other)
            self.l += [other]
        return self

    def get_op_width(self):
        return ProdTerm.op_width

    def __str__(self):
        r = "ProdTerm: " + "["+str(self.l[0])+"]"
        for t in self.l[1:]:
            r += " * ["+str(t)+"]"
        return r


class DoubleTerm(Term):
    def __init__(self, t1, t2):
        super().__init__()
        self.t1 = t1
        self.t2 = t2

    def get_lowest_container(self, x, y):
        if self.t1.contains(x, y):
            return self.t1.get_lowest_container(x, y)
        elif self.t2.contains(x, y):
            return self.t2.get_lowest_container(x, y)
        else:
            return self

    def get_smallest_container(self, x0, y0, x1, y1):
        if bbox_contains_bbox(self.get_bbox(), (x0, y0, x1, y1)):
            if self.t1.contains_region(x0, y0, x1, y1):
                return self.t1.get_smallest_container(x0, y0, x1, y1)
            elif self.t2.contains_region(x0, y0, x1, y1):
                return self.t2.get_smallest_container(x0, y0, x1, y1)
            else:
                return self, None
        else:
            return None, None

    def get_parent(self, term):
        if self.t1 == term or self.t2 == term:
            return self
        else:
            r = self.t1.get_parent(term)
            if r != None:
                return r
            else:
                return self.t2.get_parent(term)


class DivTerm(DoubleTerm):
    op_space = 10
    def __init__(self, t1, t2):
        super().__init__(t1, t2)

    def render(self, xoff = 0, yoff = 0, scaled = False):
        if scaled:
            scale = ExpTerm.scale_factor
        else:
            scale = 1
        op_space = DivTerm.op_space*scale
        self.t1.render(0, 0, scaled)
        self.t2.render(0, 0, scaled)
        w = max(self.t1.size.width, self.t2.size.width)
        h = self.t1.size.height + self.t2.size.height + op_space
        self.t1.render(xoff + (w-self.t1.size.width)/2, yoff-op_space/2 + self.t1.pos.yoff_rel-self.t1.size.height, scaled)
        self.t2.render(xoff + (w-self.t2.size.width)/2, yoff+op_space/2 + self.t2.pos.yoff_rel, scaled)
        self.size = Size(w, h)
        self.pos = Position(xoff, yoff, self.t1.size.height + op_space/2)

    def __str__(self):
        return "DivTerm: " + "["+str(self.t1)+"]" + " / " + "["+str(self.t2)+"]"


class ExpTerm(DoubleTerm):
    scale_factor = 0.6
    perc_of_t1 = 0.6
    def __init__(self, t1, t2):
        super().__init__(t1, t2)

    def render(self, xoff = 0, yoff = 0, scaled = False):
        self.t1.render(xoff, yoff, scaled)
        self.t2.render(xoff + self.t1.size.width, 0, True)
        if scaled:
            scale = ExpTerm.scale_factor
        else:
            scale = 1
        w = self.t1.size.width + self.t2.size.width
        h = self.t1.size.height*ExpTerm.perc_of_t1 + self.t2.size.height
        yoff_rel = h - self.t1.size.height/2
        self.t2.render(xoff + self.t1.size.width, yoff - yoff_rel + self.t2.pos.yoff_rel, True)
        self.size = Size(w, h)
        self.pos = Position(xoff, yoff, yoff_rel)

    def __str__(self):
        return "ExpTerm: " + "["+str(self.t1)+"]" + " ^ " + "["+str(self.t2)+"]"


ScaledFont = tkinter.font.Font(family = "arial", size = int(-def_pixel_height*ExpTerm.scale_factor))

def translate_bbox(bbox, p):
    return (bbox[0]+p[0], bbox[1]+p[1], bbox[2]+p[0], bbox[3]+p[1])

def bbox_contains_point(bbox, p):
    return bbox != None and bbox[0] <= p[0] <= bbox[2] and bbox[1] <= p[1] <= bbox[3]

def bbox_contains_bbox(a, b):
    if a == None:
        return False
    elif b == None:
        return True
    return bbox_contains_point(a, (b[0], b[1])) and bbox_contains_point(a, (b[0], b[3])) and bbox_contains_point(a, (b[2], b[1])) and bbox_contains_point(a, (b[2], b[3]))


class MarkValues:
    def __init__(self, t, sli = None):
        self.t = t
        self.sli = sli
        self.bbox = self.get_bbox()

    def get_bbox(self):
        if self.t == None:
            return None
        elif self.sli == None:
            return self.t.get_bbox()
        else:
            x0 = self.t.l[self.sli[0]].get_bbox()[0]
            x1 = self.t.l[self.sli[1]-1].get_bbox()[2]
            y0 = self.t.l[self.sli[0]].get_bbox()[1]
            y1 = self.t.l[self.sli[0]].get_bbox()[3]
            for s in self.t.l[self.sli[0]:self.sli[1]]: # hier erst ab einen spaeter starten
                y0 = min(y0, s.get_bbox()[1])
                y1 = max(y1, s.get_bbox()[3])
            return (x0, y0, x1, y1)

    def update(self, t, sli) -> bool:
        if not (self.t == t and self.sli == sli):
            self.t = t
            self.sli = sli
            self.bbox = self.get_bbox()
            print(self.bbox)
            return True
        else:
            return False


class DragValues:
    def __init__(self, mouse_down_coord, marked_values):
        self.marked_values = marked_values
        self.mouse_down_coord = mouse_down_coord
        self.old_distance = self.mouse_down_coord[0] - self.marked_values.bbox[2]

    def update(self, mouse_coord, term):
        s, _ = term.get_smallest_container(mouse_coord[0], mouse_coord[1], mouse_coord[0], mouse_coord[1]) # _ is None anyway
        if self.marked_values.sli == None:
            t = term.get_parent(self.marked_values.t)
        else:
            t = self.marked_values.t
        print("Term: ", t)
        if isinstance(t, ListTerm):
            if bbox_contains_point(t.get_bbox(), mouse_coord): # curser still on the ListTerm
                if isinstance(s, DivTerm):
                    print("is divterm")
                    pass
                elif isinstance(t, ProdTerm) and isinstance(s, ExpTerm):
                    pass
                else:
                    if self.marked_values.sli == None:
                        j = t.l.index(self.marked_values.t)
                        sli = (j, j+1)
                        self.marked_values.t = t
                    else:
                        sli = self.marked_values.sli
                    l = t.l[:sli[0]] + t.l[sli[1]:]
                    sel = t.l[sli[0]:sli[1]]
                    starting_index = sli[0]
                    i = sli[0]
                    rel_x = self.old_distance
                    curr_dist = mouse_coord[0] - self.marked_values.bbox[2] # important to take the right bound
                    curr_l = sel + l
                    if curr_dist-rel_x > 0:
                        e = 1
                    else:
                        e = -1
                    while (e < 0 and 0 < i) or (e > 0 and i < len(l)):
                        i = i + e
                        self.marked_values.t.l = l[:i] + sel + l[i:]
                        term.render(term.pos.xoff, term.pos.yoff)
                        self.marked_values.update(self.marked_values.t, (i, sli[1]-sli[0]+i))
                        new_curr_dist = mouse_coord[0] - self.marked_values.bbox[2]
                        if abs(new_curr_dist-rel_x) > abs(curr_dist-rel_x):
                            i = i - e
                            break
                    self.marked_values.t.l = l[:i] + sel + l[i:]
                    term.render(term.pos.xoff, term.pos.yoff)
                    self.marked_values.update(self.marked_values.t, (i, sli[1]-sli[0]+i))
                    return i != starting_index
        return False


class BBoxHandler:
    def __init__(self, mod, drag):
        #self.mark = mark
        self.mod = mod
        self.drag = drag


class DrawingField:
    def __init__(self, root):
        self.root = root
        self.root.update_idletasks()
        self.canvas = Canvas(root, width = root.winfo_width(), height = root.winfo_height());
        self.canvas.grid()
        self.term = None
        self.term_pos = None
        self.term_backup = None
        self.canvas.bind("<Button-1>", self.mouse_down)
        self.canvas.bind("<ButtonRelease-1>", self.mouse_up)
        self.mouse_down_coord = None
        self.marked_values = None
        self.drag_values = None
        self.mod_values = None
        self.state = None

    def redraw_marked(self):
        self.canvas.delete("marked")
        if self.marked_values != None:
            self.marked_values.bbox = self.marked_values.get_bbox()
            if self.marked_values.bbox != None:
                self.canvas.create_rectangle(self.marked_values.bbox, outline = "red", tag = "marked")

    def mouse_down(self, event):
        self.mouse_down_coord = (event.x, event.y)
        self.canvas.unbind("<B1-Motion>")
        if self.marked_values != None and self.marked_values.bbox != None and self.marked_values.bbox[0] <= event.x <= self.marked_values.bbox[2] and self.marked_values.bbox[1] <= event.y <= self.marked_values.bbox[3]:
            self.drag_values = DragValues((event.x, event.y), self.marked_values)
            if self.drag_values != None:
                self.set_state(event, "drag")
            else:
                self.set_state(event, "mod")
        else:
            self.marked_values = None
            self.drag_values = None
            self.mod_values = None
            self.set_state(event, "mark")

    def set_state(self, event, tag):
        self.canvas.unbind("<B1-Motion>")
        if tag == "mark":
            if self.marked_values != None:
                self.mark(event)
            else:
                self.set_marked_values((event.x, event.y))
            self.canvas.bind("<B1-Motion>", self.mark)
        elif tag == "mod":
            self.canvas.bind("<B1-Motion>", self.modify)
        elif tag == "drag":
            self.canvas.bind("<B1-Motion>", self.drag)

    def set_marked_values(self, p):
        if p == None:
            self.marked_values = None
        else:
            t, sli = self.term.get_smallest_container(p[0], p[1], p[0], p[1])
            self.marked_values = MarkValues(t, sli) # t==None is possible!
        self.redraw_marked()

    def mark(self, event):
        # print("mark mode")
        p = (event.x, event.y)
        if self.drag_values != None and bbox_contains_point(self.drag_values.bbox, p):
            self.set_state(event, "drag")
        elif self.mod_values != None and bbox_contains_point(self.bboxes.mod, p):
            self.set_state(event, "mod")
        else:
            (a0, b0, a1, b1) = (self.mouse_down_coord[0], self.mouse_down_coord[1], event.x, event.y)
            (a0, b0, a1, b1) = (min(a0, a1), min(b0, b1), max(a0, a1), max(b0, b1))
            term_bbox = self.term.get_bbox()
            (a0, b0, a1, b1) = (max(a0, term_bbox[0]), max(b0, term_bbox[1]), min(a1, term_bbox[2]), min(b1, term_bbox[3]))
            t, sli = self.term.get_smallest_container(a0, b0, a1, b1)
            if self.marked_values.update(t, sli):
                self.redraw_marked()

    def drag(self, event):
        # print("drag mode")
        p = (event.x, event.y)
        if self.drag_values.update((event.x, event.y), self.term):
            self.redraw()
        elif self.mod_values != None and bbox_contains_point(self.mod_values.bbox, p):
            self.set_state(event, "mod")

    def modify(self, event):
        print("mod mode")

    def update_marked_values(self, event):
        (a0, b0, a1, b1) = (self.marked_values.mouse_down_coord[0], self.marked_values.mouse_down_coord[1], event.x, event.y)
        (a0, b0, a1, b1) = (min(a0, a1), min(b0, b1), max(a0, a1), max(b0, b1))
        (a0, b0, a1, b1) = (max(a0, self.term.bbox[0]), max(b0, self.term.bbox[1]), min(a1, self.term.bbox[2]), min(b1, self.term.bbox[3]))
        if self.marked_values.update(self.term, (a0, b0, a1, b1)):
            self.redraw_marked()

    def on_click(self, event):
        # print("click coordinates:", event.x, event.y)
        self.set_marked_values((event.x, event.y))

    def mouse_up(self, event):
        self.canvas.unbind("<B1-Motion>")
        if self.mouse_down_coord[0] == event.x and self.mouse_down_coord[1] == event.y: # vllt noch nach mouse_move vorher checken
            self.on_click(event)
        elif self.drag_values != None:
            self.term.render()
            self.marked_values.bbox = self.marked_values.get_bbox()
            self.redraw()
            self.drag_values = None
        self.mouse_down_coord = None

    def clear(self):
        self.root.update_idletasks()
        self.canvas.create_rectangle(0, 0, self.canvas.winfo_width(), self.canvas.winfo_height(), fill = "white", outline = "white")

    def set_term(self, xoff, yoff, t: Term): # offset is top left corner here
        t.render()
        self.term_pos = (xoff, yoff+t.pos.yoff_rel)
        self.term = t

    def redraw(self):
        self.clear()
        self.term.render(self.term_pos[0], self.term_pos[1])
        self.draw_term(self.term)
        self.redraw_marked()

    def draw_term(self, t: Term, scaled = False): # offset is left center line
        # possible tags:
        # op
        # term
        # brace
        #returns list of id's

        canvas = self.canvas
        # canvas.create_rectangle(t.get_bbox(), outline = "red")
        if scaled:
            font = ScaledFont
            scale = ExpTerm.scale_factor
        else:
            font = UnscaledFont
            scale = 1
        print("drew term: {} at bbox: {}", t, t.get_bbox())
        canvas = self.canvas
        if scaled:
            font = ScaledFont
            scale = ExpTerm.scale_factor
        else:
            font = UnscaledFont
            scale = 1

        if isinstance(t, SingleTerm):
            i = [canvas.create_text(t.pos.xoff, t.pos.yoff, anchor = W, text = t.content, font = font, tag = "term")]
        elif isinstance(t, BraceTerm):
            i = []
            i += [canvas.create_text(t.pos.xoff, t.pos.yoff, anchor=W, text="(", font = font, tag = "brace")]
            i += self.draw_term(t.t, scaled)
            i += [canvas.create_text(t.t.pos.xoff+t.t.size.width, t.pos.yoff, anchor=W, text=")", font = font, tag = "brace")]
        elif isinstance(t, SignedTerm):
            i = []
            i += [canvas.create_line(t.pos.xoff+3*scale, t.pos.yoff, t.pos.xoff+SignedTerm.op_width*scale-3*scale, t.pos.yoff, width = 5*scale, tag = "op")]
            i += self.draw_term(t.t, scaled)
        elif isinstance(t, SumTerm):
            i = self.draw_term(t.l[0], scaled)
            for s in t.l[1:]:
                if isinstance(s, SignedTerm):
                    i += self.draw_term(s, scaled)
                else:
                    i += [canvas.create_text(s.pos.xoff, s.pos.yoff, anchor = E, text = "+", font = font, tag = "op")]
                    i += self.draw_term(s, scaled)
        elif isinstance(t, ProdTerm):
            i = self.draw_term(t.l[0], scaled)
            for s in t.l[1:]:
                i += [canvas.create_text(s.pos.xoff, s.pos.yoff, anchor = E, text = "*", font = font, tag = "op")]
                i += self.draw_term(s, scaled)
        elif isinstance(t, DivTerm):
            t1 = t.t1
            t2 = t.t2
            i = self.draw_term(t1,scaled)
            i += self.draw_term(t2, scaled)
            i += [self.canvas.create_line(t.pos.xoff, t.pos.yoff, t.pos.xoff + t.size.width, t.pos.yoff, width = DivTerm.op_space/2*scale, tag = "op")]
        elif isinstance(t, ExpTerm):
            t1 = t.t1
            t2 = t.t2
            i = self.draw_term(t1, scaled)
            i += self.draw_term(t2, True)
        return i


df = DrawingField(root)
df.clear()

s = str_to_term("(-4+5-6/(3+x)+7)/(-4+7)^(2*3)")
df.set_term(0, 200, s)
df.redraw()

root.mainloop()
