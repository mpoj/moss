# =====================================================================
# การนำเข้าไลบรารี (Libraries Import)
# =====================================================================
import tkinter as tk               # ไลบรารีหลักสำหรับสร้างหน้าต่าง GUI
from tkinter import messagebox     # ใช้สำหรับสร้างหน้าต่างแจ้งเตือน (Pop-up)
from tkinter import ttk            # ใช้สำหรับสร้างวิดเจ็ต GUI ที่ดูทันสมัยขึ้น (เช่น Combobox, Scrollbar)
from tkinter import filedialog     # ใช้สำหรับเปิดหน้าต่างเลือกโฟลเดอร์หรือไฟล์บันทึกข้อมูล
import requests                    # ไลบรารีสำหรับส่ง HTTP Request ไปยังเซิร์ฟเวอร์ (API)
import urllib3                     # ไลบรารีจัดการเครือข่ายระดับต่ำ (ใช้ร่วมกับ requests)
import base64                      # ใช้สำหรับถอดรหัสไฟล์ซอร์สโค้ดที่เข้ารหัสเป็น Base64 จากเซิร์ฟเวอร์
from datetime import datetime, timedelta  # ใช้สำหรับจัดการและคำนวณระยะเวลา (Timezone, Countdown)
import threading                   # ใช้สำหรับแยกเธรดการทำงานพื้นหลัง เพื่อไม่ให้ GUI ค้าง
import os                          # ใช้สำหรับจัดการระบบไฟล์ เช่น การสร้างโฟลเดอร์
import time                        # ใช้สำหรับการหน่วงเวลา (sleep) กรณีเชื่อมต่อล้มเหลว
import re                          # ไลบรารีสำหรับใช้งาน Regular Expression (Regex) ในการจับรูปแบบข้อความ
import collections                 # ใช้สำหรับโครงสร้างข้อมูลพิเศษ เช่น Counter เพื่อทำสถิติความถี่
import copy                        # ใช้สำหรับทำ Deepcopy โครงสร้างต้นไม้ AST
import csv                         # ใช้สำหรับสร้างและบันทึกไฟล์รายงานผล .csv
from pycparser import c_parser, c_ast  # ไลบรารีหลักสำหรับแปลงโค้ดภาษาซีให้เป็นโครงสร้างต้นไม้ (AST)
from zss import Node, simple_distance  # ไลบรารีสำหรับคำนวณระยะห่างของต้นไม้ (Tree Edit Distance)

# =====================================================================
# การตั้งค่าระบบพื้นฐาน (System Configurations)
# =====================================================================

# ปิด Warning การเชื่อมต่อ SSL ที่ไม่ปลอดภัย (กรณีเซิร์ฟเวอร์ DOMjudge ไม่ได้ติดตั้งใบรับรอง SSL ที่สมบูรณ์)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ดิกชันนารีสำหรับเก็บข้อมูลการตั้งค่าเชื่อมต่อเซิร์ฟเวอร์ที่จะรับมาจากหน้าจอ Login
config = {
    'BASE_URL': '',
    'USERNAME': '',
    'PASSWORD': ''
}

# ดิกชันนารีสำหรับเก็บข้อมูลแคช (Cache) เพื่อลดการส่ง Request ดึงข้อมูลซ้ำซ้อนจากเซิร์ฟเวอร์
CACHE_DATA = {
    'contests': []
}

# =====================================================================
# Part 1: Source Code Cleaning and AST Parsing
# (ส่วนที่ 1: การทำความสะอาดรหัสต้นฉบับและการแปลงเป็น AST)
# =====================================================================

def remove_comments(source: str) -> str:
    """
    ฟังก์ชันสำหรับลบคำอธิบาย (Comments) ทั้งหมดออกจากซอร์สโค้ดภาษาซี
    รองรับทั้งคอมเมนต์แบบบรรทัดเดียว (//) และแบบหลายบรรทัด (/* ... */)
    """
    # กำหนดรูปแบบ Regex: //.*?$ (บรรทัดเดียว) หรือ /\*.*?\*/ (หลายบรรทัด)
    pattern = re.compile(
        r'//.*?$|/\*.*?\*/',
        re.MULTILINE | re.DOTALL  # MULTILINE ให้อ่านจุดจบแต่ละบรรทัดได้, DOTALL ให้จับการขึ้นบรรทัดใหม่ได้
    )
    # ค้นหาข้อความที่ตรงกับเงื่อนไขและแทนที่ด้วยค่าว่าง (ลบทิ้ง)
    return re.sub(pattern, '', source)

def remove_preprocessor(source: str) -> str:
    """
    ฟังก์ชันสำหรับลบคำสั่ง Preprocessor ของภาษา C (เช่น #include, #define)
    เพื่อป้องกัน Error ขณะที่ pycparser ทำการสร้าง AST เนื่องจากไม่มีไฟล์ Header อ้างอิง
    """
    # แยกข้อความออกเป็นบรรทัดๆ และเก็บเฉพาะบรรทัดที่ไม่ได้ขึ้นต้นด้วยเครื่องหมาย #
    return '\n'.join(
        line for line in source.splitlines()
        if not line.lstrip().startswith('#')
    )

def clean_source(raw: str) -> str:
    """
    ฟังก์ชันตัวกลาง (Controller) สำหรับเรียกใช้กระบวนการทำความสะอาดโค้ดตามลำดับ
    """
    raw = remove_comments(raw)        # ขั้นตอนที่ 1: ลบคอมเมนต์
    raw = remove_preprocessor(raw)    # ขั้นตอนที่ 2: ลบคำสั่ง #include / #define
    return raw                        # คืนค่ารหัสต้นฉบับที่สะอาดพร้อมสำหรับการแปลงเป็น AST

def parse_c_code(source: str):
    """
    ฟังก์ชันสำหรับวิเคราะห์ไวยากรณ์และแปลงซอร์สโค้ดให้อยู่ในรูปแบบ AST (Abstract Syntax Tree)
    """
    parser = c_parser.CParser()       # สร้างออบเจกต์ตัวอ่านไวยากรณ์ภาษาซี
    try:
        # พยายามแปลงซอร์สโค้ดให้เป็น AST (รับข้อความเข้ามาเป็น string)
        ast = parser.parse(source, filename='<string>')
        return ast
    except Exception:
        # หากโค้ดเขียนผิดไวยากรณ์ร้ายแรงจนแปลงไม่ได้ (Syntax Error) ให้คืนค่า None
        return None
# =====================================================================
# Part 2: Dead Code / Unused Variable Elimination
# (ส่วนที่ 2: การค้นหาและกำจัดตัวแปรที่ไม่ได้ถูกใช้งานทิ้งไป)
# =====================================================================

class UnusedVariableRemover:
    """
    คลาสสำหรับจัดการและลบตัวแปรที่ถูกประกาศไว้แต่ไม่ได้ถูกเรียกใช้งาน (Unused Variables)
    เพื่อทำให้โครงสร้างต้นไม้ (AST) มีความกระชับและสะท้อนตรรกะที่แท้จริงของโปรแกรม
    """
    def __init__(self, ast):
        # สร้าง Set ว่างเพื่อใช้เก็บ "ชื่อตัวแปร" ที่มีการเรียกใช้งานจริงในโปรแกรม
        # การใช้ Set ช่วยให้ข้อมูลไม่ซ้ำซ้อนและค้นหาได้อย่างรวดเร็ว
        self.used_vars = set() 
        
        # ขั้นตอนที่ 1: เดินสำรวจต้นไม้เพื่อเก็บรายชื่อตัวแปรที่ถูกใช้งานทั้งหมด
        self.find_usages(ast)
        
        # ขั้นตอนที่ 2: เดินสำรวจต้นไม้อีกครั้งเพื่อตัดการประกาศตัวแปรที่ไม่อยู่ใน Set ทิ้งไป
        self.remove_unused(ast)

    def find_usages(self, node):
        """
        เมธอดสำหรับค้นหาการเรียกใช้งานตัวแปร (ID) ทั่วทั้งโครงสร้างต้นไม้
        """
        # ป้องกันข้อผิดพลาด: หากข้อมูลที่ส่งมาไม่ใช่โหนดของ AST ให้หยุดการทำงานทันที
        if not isinstance(node, c_ast.Node): return
        
        # หากโหนดปัจจุบันเป็นตัวแทนของชื่อตัวแปร (Identifier)
        if isinstance(node, c_ast.ID):
            # ให้บันทึกชื่อตัวแปรนั้นลงใน Set ของตัวแปรที่มีการใช้งานจริง
            self.used_vars.add(node.name)
            
        # วนลูปเพื่อสำรวจโหนดย่อยทั้งหมดที่อยู่ภายใต้โหนดปัจจุบัน (ลงลึกไปทีละชั้น)
        for _, child in node.children():
            self.find_usages(child)  # เรียกใช้ตัวเองซ้ำ (Recursion) เพื่อสำรวจให้ครบทุกกิ่ง

    def remove_unused(self, node):
        """
        เมธอดสำหรับตัดโหนดการประกาศตัวแปร (Declaration) ที่ไม่ได้ถูกใช้งานออกไปจากต้นไม้
        """
        # ป้องกันข้อผิดพลาด: หากข้อมูลที่ส่งมาไม่ใช่โหนดของ AST ให้หยุดการทำงาน
        if not isinstance(node, c_ast.Node): return
        
        # วนลูปสำรวจทุกแอตทริบิวต์ (คุณลักษณะ) ที่โหนดปัจจุบันครอบครองอยู่ผ่าน __slots__
        for attr in node.__slots__:
            val = getattr(node, attr, None) # ดึงค่าที่อยู่ในแอตทริบิวต์นั้นออกมา
            
            # กรณีที่ 1: หากข้อมูลภายในเป็นรายการของโหนด (List of nodes) เช่น บล็อกคำสั่ง
            if isinstance(val, list):
                new_list = [] # สร้างรายการใหม่เพื่อคัดลอกเฉพาะโหนดที่มีประโยชน์มาเก็บไว้
                
                for item in val:
                    # หากโหนดย่อยเป็นการประกาศ (Declaration) เช่น การสร้างตัวแปรหรือฟังก์ชัน
                    if isinstance(item, c_ast.Decl):
                        
                        # หากเป็นการประกาศฟังก์ชัน (Function Declaration)
                        if isinstance(item.type, c_ast.FuncDecl):
                            new_list.append(item) # ให้เก็บรักษาไว้เสมอ ห้ามลบ
                            continue
                        
                        # หากเป็นการประกาศตัวแปร และชื่อตัวแปรนั้น "ไม่ได้ถูกบันทึก" ใน used_vars
                        if item.name and item.name not in self.used_vars:
                            continue # ข้ามคำสั่ง append ด้านล่างไปเลย (ทำให้โหนดนี้ถูกลบทิ้งไป)
                            
                    # ทำความสะอาดโหนดย่อยให้ลึกลงไปอีก (Recursion)
                    self.remove_unused(item)
                    # นำโหนดที่ผ่านการคัดกรองความสะอาดแล้ว ใส่เข้าไปในรายการใหม่
                    new_list.append(item)
                
                # เขียนทับแอตทริบิวต์เดิม ด้วยรายการใหม่ที่ไม่มีตัวแปรขยะแล้ว
                setattr(node, attr, new_list)
                
            # กรณีที่ 2: หากข้อมูลภายในเป็นโหนดเดี่ยวๆ
            elif isinstance(val, c_ast.Node):
                # ส่งโหนดนั้นเข้าไปทำความสะอาดตัวเองต่อ (Recursion)
                self.remove_unused(val)
                
        # ส่งคืนโครงสร้างต้นไม้ที่ถูกตัดแต่งกิ่งให้สะอาดและกระชับที่สุดกลับไป
        return node
# =====================================================================
# Part 3: Function Inlining & AST Flattening
# =====================================================================

class FunctionInliner:
    """
    คลาสสำหรับทำ Function Inlining 
    ช่วยขยายโครงสร้างโปรแกรมที่ถูกแยกเขียนเป็นฟังก์ชันย่อย ให้กลับมารวมเป็นลำดับคำสั่งที่ต่อเนื่องกัน
    เพื่อประโยชน์ในการวิเคราะห์ความคล้ายคลึงของอัลกอริทึม
    """
    def __init__(self, ast):
        self.funcs = {} # ดิกชันนารีสำหรับจัดเก็บชื่อและเนื้อหาของฟังก์ชันย่อยทั้งหมด
        new_ext = []    # ลิสต์สำหรับเก็บองค์ประกอบที่ไม่ใช่ฟังก์ชันย่อย (เช่น ฟังก์ชัน main)
        
        # วนลูปสำรวจองค์ประกอบระดับนอกสุด (ext) ของต้นไม้ AST
        for ext in getattr(ast, 'ext', []):
            # หากองค์ประกอบนี้คือ "การประกาศฟังก์ชัน" และ "ไม่ใช่ฟังก์ชัน main"
            if isinstance(ext, c_ast.FuncDef) and ext.decl.name != 'main':
                # ให้เก็บเนื้อหาของฟังก์ชัน (body) ลงในดิกชันนารี โดยใช้ชื่อฟังก์ชันเป็นคีย์
                self.funcs[ext.decl.name] = ext.body
            else:
                # หากไม่ใช่ (เช่น เป็น main หรือตัวแปรโกลบอล) ให้เก็บรักษาไว้ในลิสต์หลักตามเดิม
                new_ext.append(ext)
                
        # อัปเดตโครงสร้าง AST ให้เหลือแค่ส่วนหลัก (ตัดฟังก์ชันย่อยที่แยกเก็บไปแล้วออก)
        if hasattr(ast, 'ext'):
            ast.ext = new_ext
            
    def inline(self, node):
        """
        เมธอดสำหรับสำรวจต้นไม้ และแทนที่การเรียกใช้ฟังก์ชันด้วยเนื้อหาจริง
        """
        # ป้องกันข้อผิดพลาด: หากไม่ใช่โหนดของ AST ให้ส่งคืนค่าเดิมกลับไปทันที
        if not isinstance(node, c_ast.Node): return node
        
        # ตรวจสอบว่าโหนดปัจจุบันคือ "โหนดการเรียกใช้งานฟังก์ชัน" (Function Call) หรือไม่
        if isinstance(node, c_ast.FuncCall):
            # ดึงชื่อฟังก์ชันที่ถูกเรียกใช้ออกมาอย่างปลอดภัย
            func_name = getattr(node.name, 'name', None)
            
            # หากชื่อฟังก์ชันที่เรียกใช้นี้ มีข้อมูลเนื้อหาเก็บไว้ในฐานข้อมูลของเรา
            if func_name in self.funcs:
                # ทำการคัดลอกเนื้อหาฟังก์ชันต้นฉบับแบบลึก (Deep Copy) เพื่อไม่ให้กระทบโครงสร้างตั้งต้น
                body_copy = copy.deepcopy(self.funcs[func_name])
                # ส่งเนื้อหาที่คัดลอกมาไปทำ Inlining ซ้ำอีกรอบ (เผื่อมีการเรียกฟังก์ชันซ้อนกัน) 
                # แล้วส่งคืนเพื่อแทนที่โหนดการเรียกใช้ (FuncCall) นี้เลย
                return self.inline(body_copy)
                
        # หากไม่ใช่โหนดการเรียกใช้งานฟังก์ชัน ให้วนลูปสำรวจทุกแอตทริบิวต์ของโหนดผ่าน __slots__
        for attr in node.__slots__:
            val = getattr(node, attr, None) # ดึงค่าของแอตทริบิวต์นั้นออกมา
            
            # กรณีที่ค่าภายในเป็นรูปแบบลิสต์ของโหนด (เช่น บล็อกของกลุ่มคำสั่ง)
            if isinstance(val, list):
                new_list = [] # สร้างลิสต์ใหม่มารองรับ
                
                # วนลูปดึงโหนดย่อยทีละตัว
                for item in val:
                    # ส่งโหนดย่อยไปผ่านกระบวนการ Inlining และนำผลลัพธ์มาเก็บในลิสต์ใหม่
                    new_list.append(self.inline(item))
                # เขียนทับแอตทริบิวต์เดิม ด้วยลิสต์ใหม่ที่ทำ Inlining เรียบร้อยแล้ว
                setattr(node, attr, new_list)
                
            # กรณีที่ค่าภายในเป็นโหนดเดี่ยวๆ
            elif isinstance(val, c_ast.Node):
                # ส่งโหนดนั้นไปทำ Inlining แล้วนำผลลัพธ์มาเขียนทับตำแหน่งเดิมทันที
                setattr(node, attr, self.inline(val))
                
        # คืนค่าโหนดที่ผ่านการขยายโครงสร้างจนสมบูรณ์แล้วกลับไป
        return node

# =====================================================================
# Part 4: Commutative Operator Sorting
# (ส่วนที่ 4: การจัดเรียงตัวดำเนินการที่มีคุณสมบัติการสลับที่ได้ให้เป็นมาตรฐานเดียวกัน)
# =====================================================================

def sort_commutative_ops(node):
    """
    ฟังก์ชันสำหรับดัดโครงสร้างต้นไม้ (AST) ของนิพจน์ที่สลับที่ได้ (เช่น A+B หรือ B+A) 
    ให้เรียงลำดับในรูปแบบเดียวกันเสมอ เพื่อลดความแตกต่างเล็กๆ น้อยๆ 
    ที่เกิดจากสไตล์การเขียนโค้ดของผู้เขียนแต่ละคน
    """
    # ป้องกันข้อผิดพลาด: ตรวจสอบว่าเป็นโหนดของ AST จริงๆ หรือไม่ หากไม่ใช่ให้หยุดการทำงาน
    if not isinstance(node, c_ast.Node): return
    
    # วนลูปสำรวจโหนดย่อยทั้งหมดที่อยู่ภายใต้โหนดปัจจุบัน
    for _, child in node.children():
        # เรียกใช้งานตัวเอง (Recursion) เพื่อมุดลงไปจัดเรียงโหนดย่อยที่อยู่ลึกลงไปให้เสร็จก่อน 
        # (เป็นการทำงานแบบ Post-order traversal)
        sort_commutative_ops(child)
        
    # เมื่อโหนดย่อยจัดเรียงเสร็จแล้ว กลับมาตรวจสอบโหนดปัจจุบันว่าเป็นตัวดำเนินการทวิภาค (BinaryOp) หรือไม่
    if isinstance(node, c_ast.BinaryOp):
        # ตรวจสอบว่าเครื่องหมายของโหนดนี้ มีคุณสมบัติการสลับที่ได้ทางคณิตศาสตร์หรือตรรกศาสตร์หรือไม่
        if node.op in ('+', '*', '==', '!=', '&', '|', '^', '&&', '||'):
            # สร้างตัวแทนรูปแบบข้อความ (String representation) ของโหนดฝั่งซ้ายและฝั่งขวา
            left_str = repr(node.left)
            right_str = repr(node.right)
            
            # เปรียบเทียบข้อความตามลำดับตัวอักษร 
            # หากตัวแทนของฝั่งขวามีลำดับตัวอักษรมาก่อนฝั่งซ้าย
            if right_str < left_str:
                # ทำการสลับตำแหน่งโหนดซ้ายและขวาในต้นไม้ AST ทันที
                # เพื่อให้โครงสร้างถูกจัดเรียงในรูปแบบที่เป็นมาตรฐานเดียวกันเสมอ
                node.left, node.right = node.right, node.left


# =====================================================================
# Part 5: AST Representation Normalization
# (ส่วนที่ 5: การปรับรูปแบบของโครงสร้างต้นไม้ให้เป็นมาตรฐานเดียวกัน)
# =====================================================================

def normalize_ast_repr(ast_obj):
    """
    ฟังก์ชันสำหรับแปลงวัตถุโครงสร้างต้นไม้ (AST) ให้กลายเป็นข้อความมาตรฐาน
    โดยลบความแตกต่างเล็กๆ น้อยๆ เช่น การตั้งชื่อตัวแปร หรือการจัดรูปแบบการเว้นวรรค
    เพื่อให้พร้อมสำหรับการเปรียบเทียบความเหมือนของโครงสร้างแบบตรงไปตรงมา
    """
    # ป้องกันข้อผิดพลาด: หากออบเจกต์ที่รับมามีค่าว่าง ให้ส่งคืนข้อความว่างกลับไป
    if ast_obj is None: return ''
    
    # ดึงค่าตัวแทนในรูปแบบข้อความ (String Representation) ของออบเจกต์ AST ออกมา
    ast_string = ast_obj.__repr__()
    
    # ใช้ Regex ค้นหาแอตทริบิวต์ 'name' ที่เก็บชื่อตัวแปร (เช่น name='x' หรือ name='sum')
    # แล้วแทนที่ด้วยคำว่า name='ID' ทั้งหมด เพื่อลบเอกลักษณ์การตั้งชื่อ (Anonymization)
    ast_string = re.sub(r"name='[^']+'", "name='ID'", ast_string)
    
    # ใช้ Regex ค้นหาและลบช่องว่าง (Whitespace) รวมถึงการขึ้นบรรทัดใหม่ทั้งหมด (\s+) 
    # เพื่อยุบข้อความให้ติดกันเป็นบรรทัดเดียว ตัดปัญหาการจัดรูปแบบโค้ดที่แตกต่างกัน
    ast_string = re.sub(r'\s+', '', ast_string)
    
    # คืนค่าข้อความที่ผ่านการทำมาตรฐาน (Normalization) เรียบร้อยแล้ว
    return ast_string

# =====================================================================
# Part 6: Identifier Mapping
# (ส่วนที่ 6: การสร้างแผนผังจับคู่ชื่อตัวแปร)
# =====================================================================

def build_id_map(node: c_ast.Node, id_map=None, counter=None):
    """
    ฟังก์ชันสำหรับสร้างแผนผังความสัมพันธ์ (Map) ระหว่างชื่อตัวแปรดั้งเดิม กับชื่อตัวแปรมาตรฐาน
    เพื่อจัดการกับปัญหาที่นักศึกษาคัดลอกโค้ดแต่ใช้วิธี 'เปลี่ยนชื่อตัวแปร' (Variable Renaming)
    """
    # กำหนดค่าเริ่มต้นให้กับพารามิเตอร์ หากเป็นการเรียกฟังก์ชันครั้งแรก
    if id_map is None: id_map = {} # ใช้ดิกชันนารีเก็บแผนผัง (เช่น {'x': 'VAR1', 'y': 'VAR2'})
    if counter is None: counter = [1] # ใช้ลิสต์เก็บตัวนับเพื่อให้ค่าอัปเดตต่อเนื่องเมื่อเรียกฟังก์ชันซ้ำ (Pass by Reference)
    
    # ตรวจสอบว่าโหนดปัจจุบันคือชื่อตัวแปร (Identifier) หรือไม่
    if isinstance(node, c_ast.ID):
        name = node.name # ดึงชื่อตัวแปรดั้งเดิมออกมา
        
        # หากชื่อตัวแปรนี้เพิ่งเคยเจอเป็นครั้งแรก (ยังไม่ถูกบันทึกในแผนผัง)
        if name not in id_map:
            # ทำการจับคู่ชื่อเดิม เข้ากับชื่อมาตรฐานใหม่ เช่น 'VAR1', 'VAR2' ตามลำดับ
            id_map[name] = f'VAR{counter[0]}'
            # เพิ่มค่าตัวนับขึ้น 1 เพื่อเตรียมไว้ใช้กับตัวแปรหน้าตาใหม่ตัวต่อไป
            counter[0] += 1
            
    # วนลูปสำรวจโหนดย่อยทั้งหมดภายใต้โหนดปัจจุบัน
    for _, child in node.children():
        # เรียกใช้งานตัวเอง (Recursion) เพื่อส่งผ่านแผนผังและตัวนับลงไปสำรวจและบันทึกชื่อตัวแปรให้ครบทั้งต้นไม้
        build_id_map(child, id_map, counter)
        
    # คืนค่าแผนผังความสัมพันธ์ (Dictionary) ที่เก็บข้อมูลครบถ้วนแล้วกลับไป
    return id_map
# =====================================================================
# Part 7: AST Node Labeling
# (ส่วนที่ 7: การสร้างป้ายชื่อและระบุเอกลักษณ์ให้กับโหนดในโครงสร้างต้นไม้)
# =====================================================================

def node_label(node: c_ast.Node, id_map) -> str:
    """
    ฟังก์ชันสำหรับดึงคุณลักษณะเด่นของโหนดแต่ละประเภทออกมาสร้างเป็น 'ป้ายชื่อ' (Label)
    เพื่อให้การคำนวณ Tree Edit Distance สามารถแยกแยะความแตกต่างของโหนดที่ทำหน้าที่ต่างกันได้
    """
    # ดึงชื่อคลาส (ชนิดของโหนด) มาเก็บเป็นค่าพื้นฐาน เช่น 'If', 'For', 'Assignment'
    cls = node.__class__.__name__
    
    # กรณีเป็นโหนดการเรียกใช้ฟังก์ชัน
    if isinstance(node, c_ast.FuncCall):
        # ดึงชื่อฟังก์ชันที่ถูกเรียกใช้ออกมา
        name = getattr(node.name, 'name', None)
        # ส่งคืนป้ายชื่อพร้อมชื่อฟังก์ชัน (เช่น 'FuncCall:printf') หากไม่มีชื่อให้คืนแค่ 'FuncCall'
        return f'FuncCall:{name}' if name else 'FuncCall'
        
    # กรณีเป็นโหนดตัวดำเนินการทวิภาค (เช่น บวก ลบ คูณ หาร)
    if isinstance(node, c_ast.BinaryOp):
        # ส่งคืนป้ายชื่อพร้อมเครื่องหมายการคำนวณ (เช่น 'BinaryOp:+')
        return f'BinaryOp:{node.op}'
        
    # กรณีเป็นโหนดชื่อตัวแปร
    if isinstance(node, c_ast.ID):
        # ค้นหาชื่อมาตรฐาน (VAR1, VAR2) จากแผนผังที่เตรียมไว้ หากไม่พบให้ใช้คำว่า 'VAR'
        canon = id_map.get(node.name, 'VAR')
        # ส่งคืนป้ายชื่อพร้อมชื่อมาตรฐาน (เช่น 'ID:VAR1')
        return f'ID:{canon}'
        
    # กรณีเป็นโหนดค่าคงที่ (ตัวเลข, ตัวอักษร)
    if isinstance(node, c_ast.Constant):
        # ส่งคืนป้ายชื่อพร้อมประเภทของค่าคงที่ (เช่น 'Const:int')
        return f'Const:{node.type}'
        
    # กรณีเป็นโหนดการประกาศตัวแปรหรือฟังก์ชัน
    if isinstance(node, c_ast.Decl):
        # ดึงชนิดของข้อมูลที่ประกาศ (เช่น FuncDecl, TypeDecl)
        typ = node.type.__class__.__name__
        # ค้นหาชื่อมาตรฐานจากแผนผัง หรือใช้ชื่อเดิมหากไม่พบ
        canon = id_map.get(node.name, node.name)
        # ส่งคืนป้ายชื่อแบบละเอียดที่ระบุทั้งชื่อและชนิด (เช่น 'Decl:VAR1:TypeDecl')
        return f'Decl:{canon}:{typ}'
        
    # หากโหนดไม่เข้าข่ายเงื่อนไขพิเศษด้านบน ให้ส่งคืนแค่ชื่อคลาสพื้นฐาน
    return cls

# =====================================================================
# Part 8: AST to ZSS Tree Conversion
# (ส่วนที่ 8: การแปลงโครงสร้าง AST ให้เป็นโครงสร้างสำหรับอัลกอริทึม ZSS)
# =====================================================================

def ast_to_tree(node: c_ast.Node, id_map):
    """
    ฟังก์ชันสำหรับแปลงวัตถุ AST ของไลบรารี pycparser 
    ให้กลายเป็นโครงสร้างข้อมูลแบบทูเพิล (Tuple) เรียบง่ายในรูปแบบ: (ป้ายชื่อ, [รายการโหนดย่อย])
    """
    # ป้องกันข้อผิดพลาด: หากโหนดว่างเปล่าให้คืนค่า None
    if node is None: return None
    
    # สร้างป้ายชื่อของโหนดปัจจุบันโดยเรียกใช้ฟังก์ชัน node_label
    label = node_label(node, id_map)
    children = [] # สร้างลิสต์เพื่อเตรียมรองรับโหนดย่อย
    
    # วนลูปสำรวจโหนดย่อยทั้งหมดของโหนดปัจจุบัน
    for _, child in node.children():
        # เรียกใช้ตัวเองซ้ำ (Recursion) เพื่อแปลงโหนดย่อยให้เป็นทูเพิลเช่นกัน
        ct = ast_to_tree(child, id_map)
        # หากแปลงโหนดย่อยสำเร็จ ให้นำมาต่อท้ายในลิสต์ children
        if ct: children.append(ct)
        
    # คืนค่ากลับไปเป็นทูเพิลที่ประกอบด้วย (ป้ายชื่อ, รายการโหนดย่อย)
    return (label, children)

def tree_to_zss(tree):
    """
    ฟังก์ชันสำหรับแปลงโครงสร้างทูเพิล ให้กลายเป็นออบเจกต์ Node ตามมาตรฐานของไลบรารี zss
    เพื่อให้พร้อมสำหรับการนำไปเข้าสมการคำนวณ Tree Edit Distance ต่อไป
    """
    # ป้องกันข้อผิดพลาด: หากโครงสร้างต้นไม้ว่างเปล่าให้คืนค่า None
    if tree is None: return None
    
    # กรณีที่รับข้อมูลมาเป็นรูปแบบลิสต์ (เช่น มีต้นไม้หลายต้นระดับเดียวกัน)
    if isinstance(tree, list):
        z_node = Node('Root') # สร้างโหนดรากเทียม (Dummy Root) ขึ้นมาครอบไว้
        for t in tree:
            # แปลงโหนดย่อยแต่ละตัวเป็น zss Node และเพิ่มเป็นลูกของโหนด Root
            z_node.addkid(tree_to_zss(t))
        return z_node
        
    # แตกข้อมูลทูเพิลออกเป็น 2 ส่วน คือ ป้ายชื่อ (label) และ รายการโหนดย่อย (children)
    label, children = tree
    # สร้างออบเจกต์ Node ของ zss โดยใช้ป้ายชื่อที่แยกมาได้
    z_node = Node(label)
    
    # วนลูปจัดการโหนดย่อย
    for ch in children:
        if ch:
            # เรียกใช้ตัวเองซ้ำ (Recursion) เพื่อแปลงโหนดย่อยเป็น zss Node และเพิ่มเป็นลูกของโหนดปัจจุบัน
            z_node.addkid(tree_to_zss(ch))
            
    # คืนค่าออบเจกต์ Node ของ zss ที่สมบูรณ์แบบพร้อมใช้งานกลับไป
    return z_node

# =====================================================================
# Part 9: Feature Extraction & Explainability
# (ส่วนที่ 9: การสกัดจุดเด่นของโค้ดและการสร้างข้อความอธิบายความคล้ายคลึง)
# =====================================================================

def extract_features(ast_root: c_ast.Node):
    """
    ฟังก์ชันสำหรับเดินสำรวจโครงสร้างต้นไม้ (AST) และนับความถี่ขององค์ประกอบต่างๆ
    เพื่อสกัดออกมาเป็น 'ลักษณะเฉพาะ' (Features) ของโปรแกรมนั้นๆ
    """
    # สร้างตัวเก็บสถิติ (Counter) ที่สามารถเพิ่มค่าอัตโนมัติเมื่อเจอคีย์ใหม่
    counter = collections.Counter()
    
    def visit(node):
        """
        ฟังก์ชันย่อย (Helper) สำหรับเดินสำรวจโหนดทุกตัวแบบ 재귀 (Recursion)
        """
        # 1. นับประเภทของโหนด (เช่น 'If', 'For', 'BinaryOp')
        cls = node.__class__.__name__
        counter[cls] += 1
        
        # 2. นับการเรียกใช้ฟังก์ชันแบบเจาะจงชื่อ
        if isinstance(node, c_ast.FuncCall):
            name = getattr(node.name, 'name', None)
            if name: 
                # เก็บสถิติโดยใช้คำนำหน้า FUNC: เพื่อแยกออกจากประเภทโหนดปกติ
                counter[f'FUNC:{name}'] += 1
                
        # 3. นับตัวดำเนินการแบบเจาะจงเครื่องหมาย
        if isinstance(node, c_ast.BinaryOp):
            # เก็บสถิติโดยใช้คำนำหน้า OP: 
            counter[f'OP:{node.op}'] += 1
            
        # วนลูปส่งโหนดย่อยเข้าไปสำรวจต่อให้ครบทั้งต้นไม้
        for _, child in node.children():
            visit(child)
            
    # สั่งเริ่มการสำรวจจากโหนดราก (Root) ของ AST
    visit(ast_root)
    # คืนค่าสถิติความถี่ทั้งหมดที่นับได้กลับไป
    return counter

def explain_similarity(nameA, featsA, nameB, featsB):
    """
    ฟังก์ชันสำหรับนำสถิติลักษณะเฉพาะ (Features) ของ 2 โปรแกรมมาเทียบกัน
    เพื่อสร้างข้อความอธิบาย (Explainability) ว่าทำไมระบบถึงมองว่าโค้ด 2 ชุดนี้คล้ายกัน
    """
    # หา "จุดตัด" (Intersection) ของลักษณะเฉพาะที่มีเหมือนกันในทั้ง 2 โปรแกรม
    common_keys = set(featsA.keys()) & set(featsB.keys())
    reasons = [] # ลิสต์สำหรับเก็บประโยคเหตุผล
    
    # 1. ตรวจสอบการใช้คำสั่งควบคุมทิศทาง (Control Flow) ที่สำคัญ
    for kind, label_th in [('If', 'if'), ('For', 'for'), ('While', 'while'), ('Switch', 'switch')]:
        if kind in common_keys:
            # หากมีการใช้คำสั่งประเภทนี้เหมือนกัน ให้ระบุจำนวนครั้งที่พบของทั้งสองโปรแกรมลงในข้อความ
            reasons.append(f'- มีคำสั่ง {label_th} เหมือนกัน ประมาณ {featsA[kind]} / {featsB[kind]} ครั้ง')
            
    # 2. ตรวจสอบการเรียกใช้ฟังก์ชัน (ดึงเฉพาะคีย์ที่ขึ้นต้นด้วย 'FUNC:')
    common_funcs = [k for k in common_keys if k.startswith('FUNC:')]
    if common_funcs:
        # ตัดคำว่า 'FUNC:' ออกเพื่อให้เหลือแค่ชื่อฟังก์ชันสำหรับนำไปแสดงผล
        func_names = [k.split('FUNC:')[1] for k in common_funcs]
        reasons.append(f'- เรียกใช้ฟังก์ชันชุดเดียวกัน {func_names}')
        
    # 3. ตรวจสอบการใช้ตัวดำเนินการ (ดึงเฉพาะคีย์ที่ขึ้นต้นด้วย 'OP:')
    common_ops = [k for k in common_keys if k.startswith('OP:')]
    if common_ops:
        # ตัดคำว่า 'OP:' ออกเพื่อให้เหลือแค่เครื่องหมายสำหรับนำไปแสดงผล
        op_list = [k.split('OP:')[1] for k in common_ops]
        reasons.append(f'- ใช้ Operator คล้ายกัน {op_list}')
        
    # หากไม่พบจุดร่วมเด่นๆ ใน 3 ข้อด้านบนเลย (อาจจะคล้ายกันที่โครงสร้างอื่นๆ)
    if not reasons:
        reasons.append('- โครงสร้างโดยรวมคล้ายกัน ควรเปิดเทียบทีละบรรทัด')
        
    # นำประโยคเหตุผลทั้งหมดมารวมกันโดยคั่นด้วยการขึ้นบรรทัดใหม่ (\n) แล้วส่งคืน
    return '\n'.join(reasons)

# =====================================================================
# Part 10: Network Utilities (Updated to use requests)
# (ส่วนที่ 10: ระบบจัดการเครือข่ายและการดึงข้อมูล อัปเดตเพื่อใช้ไลบรารี requests)
# =====================================================================

def fetch_data(endpoint, retries=3):
    """
    ฟังก์ชันแกนหลักสำหรับส่งคำร้องขอ (HTTP Request) ไปยัง API ของเซิร์ฟเวอร์ DOMjudge
    พร้อมระบบพยายามเชื่อมต่อซ้ำ (Retry Mechanism) กรณีเครือข่ายมีปัญหา
    """
    # สร้าง URL ที่สมบูรณ์ โดยลบเครื่องหมาย / ท้าย BASE_URL ออกก่อน (ป้องกัน // ซ้อนกัน) แล้วค่อยต่อด้วย endpoint
    url = f'{config["BASE_URL"].rstrip("/")}{endpoint}'
    # ดึงข้อมูลบัญชีผู้ใช้และรหัสผ่านจากดิกชันนารีตั้งค่า
    user = config["USERNAME"]
    pwd = config["PASSWORD"]
    
    # วนลูปพยายามเชื่อมต่อตามจำนวนรอบ (retries) ที่กำหนดไว้ (ค่าเริ่มต้นคือ 3 รอบ)
    for attempt in range(retries):
        try:
            # ใช้ requests.get เพื่อดึงข้อมูล 
            # - auth=(user, pwd) ทำ Basic Authentication ให้ท้นที
            # - timeout=10 ป้องกันโปรแกรมค้างหากเซิร์ฟเวอร์ไม่ตอบสนองภายใน 10 วินาที
            # - verify=False ข้ามการตรวจสอบ SSL Certificate (จำเป็นสำหรับเซิร์ฟเวอร์จำลองหรือภายในมหาวิทยาลัย)
            res = requests.get(url, auth=(user, pwd), timeout=10, verify=False)
            
            # ตรวจสอบสถานะ (HTTP Status Code) ถ้ารหัสเป็น 4xx หรือ 5xx จะโยน Exception ออกมา
            res.raise_for_status()
            
            # หากสำเร็จ จะแปลงข้อความที่ได้ให้เป็นโครงสร้างข้อมูล JSON และส่งคืนทันที
            return res.json()
            
        except requests.exceptions.RequestException:
            # หากเกิดปัญหาเรื่องการเชื่อมต่อ (เช่น เน็ตหลุด, Timeout) ให้หน่วงเวลา 2 วินาทีก่อนลองใหม่ในรอบถัดไป
            time.sleep(2)
        except Exception:
            # หากเป็น Error ร้ายแรงอื่นๆ ที่ไม่ใช่เรื่องเครือข่าย ให้หลุดออกจากลูป (ยกเลิกการลองใหม่)
            break
            
    # หากพยายามจนครบโควตาแล้วยังไม่สำเร็จ ให้คืนค่า None
    return None

def calculate_time_remaining(end_time_str):
    """
    ฟังก์ชันสำหรับคำนวณและจัดรูปแบบเวลาที่เหลืออยู่ของการแข่งขัน (Countdown Timer)
    """
    # ป้องกันข้อผิดพลาด: หากไม่มีเวลาสิ้นสุดระบุไว้ ให้ถือว่าไม่จำกัดเวลา
    if not end_time_str: return 'Unlimited'
    try:
        # แปลงข้อความเวลามาตรฐาน ISO 8601 ให้เป็นออบเจกต์ datetime
        end_time = datetime.fromisoformat(end_time_str)
        # ดึงเวลาปัจจุบันของเครื่อง โดยอ้างอิง Timezone เดียวกับเวลาเป้าหมายเพื่อความแม่นยำ
        now = datetime.now(end_time.tzinfo)
        
        # หากเวลาปัจจุบันเลยเวลาสิ้นสุดไปแล้ว ให้แสดงสถานะว่า Ended
        if now > end_time: return 'Ended'
        
        # คำนวณส่วนต่างของเวลา
        remaining = end_time - now
        total_seconds = int(remaining.total_seconds()) # แปลงเป็นจำนวนวินาทีรวม
        
        # ใช้ divmod เพื่อคำนวณหาจำนวนชั่วโมง และเศษวินาทีที่เหลือ
        hours, remainder = divmod(total_seconds, 3600)
        # นำเศษวินาทีมา divmod อีกครั้งเพื่อหาจำนวนนาที และวินาที
        minutes, seconds = divmod(remainder, 60)
        
        # คำนวณหาจำนวนวัน (นำชั่วโมงหารปัดเศษด้วย 24)
        days = hours // 24
        hours = hours % 24 # หาเศษชั่วโมงที่เหลือจากจำนวนวัน
        
        # หากเวลาเหลือมากกว่า 1 วัน ให้แสดงรูปแบบ "วัน และ ชั่วโมง" (เช่น 2d 5h)
        if days > 0: return f'{days}d {hours}h'
        
        # หากเวลาน้อยกว่า 1 วัน ให้แสดงรูปแบบ HH:MM:SS โดยเติม 0 ข้างหน้าให้ครบ 2 หลักเสมอ
        return f'{hours:02}:{minutes:02}:{seconds:02}'
    except: 
        # หากข้อมูลเวลาผิดเพี้ยนจนคำนวณไม่ได้ ให้ส่งคืนข้อความ Unknown ป้องกันโปรแกรมแครช
        return 'Unknown'

def format_timestamp(iso_time):
    """
    ฟังก์ชันสำหรับจัดรูปแบบข้อความเวลา (Timestamp) ให้ดูง่ายขึ้น
    พร้อมปรับชดเชยเวลา (Timezone Offset)
    """
    try:
        # แปลงข้อความ ISO ให้เป็นออบเจกต์ datetime
        dt = datetime.fromisoformat(iso_time)
        # ทำการบวกเวลาเพิ่ม 6 ชั่วโมง (เพื่อปรับชดเชยให้ตรงกับเขตเวลาที่กำหนดไว้ในระบบ)
        dt = dt + timedelta(hours=6)
        # คืนค่าเวลาในรูปแบบ ชั่วโมง:นาที:วินาที
        return dt.strftime('%H:%M:%S')
    except:
        # หากแปลงไม่สำเร็จ ให้คืนค่าข้อความต้นฉบับกลับไป
        return iso_time

def process_check_data(callback_success, callback_error):
    """
    ฟังก์ชันตัวกลางสำหรับดึงข้อมูลการแข่งขันทั้งหมด และคัดกรองข้อมูลให้เป็นระเบียบ
    ถูกออกแบบมาให้ทำงานในเธรดเบื้องหลัง และส่งผลลัพธ์กลับไปยัง GUI ผ่าน Callback Function
    """
    try:
        # ดึงข้อมูลรายชื่อการแข่งขันจาก API
        contests = fetch_data('/api/v4/contests')
        
        # หากดึงข้อมูลไม่ได้ (อาจจะเน็ตหลุด หรือรหัสผ่านผิด)
        if contests is None:
            # เรียกใช้ฟังก์ชัน Callback สำหรับแจ้ง Error กลับไปยังหน้าต่างหลัก
            callback_error('Failed to retrieve contests or unauthorized.')
            return
            
        processed_contests = [] # ลิสต์สำหรับเก็บข้อมูลการแข่งขันที่ผ่านการจัดระเบียบแล้ว
        
        # วนลูปจัดการข้อมูลการแข่งขันทีละรายการ
        for c in contests:
            c_id = c['id']
            # สร้างดิกชันนารีเก็บข้อมูลเฉพาะส่วนที่จำเป็นสำหรับแสดงผลบนหน้าจอ
            processed_contests.append({
                'id': c_id,
                # ดึงชื่อการแข่งขัน หากไม่มีชื่อให้ใช้รหัสการแข่งขันแทน
                'name': c.get('name', str(c_id)),
                'end_time_raw': c.get('end_time'),
                # ส่งเวลาสิ้นสุดไปคำนวณเวลาที่เหลือ เพื่อนำมาแสดงผล
                'time_display': calculate_time_remaining(c.get('end_time')),
                'problem_count': '?', # กำหนดค่าเริ่มต้นเป็น ? (จะถูกอัปเดตเมื่อดึงข้อมูลโจทย์)
                'problems_data': None # สร้างคีย์เผื่อไว้เก็บข้อมูลโจทย์และสถิติในภายหลัง
            })
            
        # เมื่อจัดระเบียบข้อมูลเสร็จแล้ว เรียกฟังก์ชัน Callback ส่งข้อมูลกลับไปให้หน้าต่างหลักนำไปสร้างรายการ
        callback_success(processed_contests)
        
    except Exception as e:
        # หากมีข้อผิดพลาดรุนแรงระหว่างทาง ให้ดักจับและส่งข้อความ Error กลับไปแสดงผล
        callback_error(str(e))

# =====================================================================
# Part 11: Main Application GUI
# (ส่วนที่ 11: คลาสหลักสำหรับจัดการหน้าต่างโปรแกรมและส่วนติดต่อผู้ใช้งาน)
# =====================================================================

class JudgeApp:
    """
    คลาสหลักของโปรแกรม ทำหน้าที่บริหารจัดการหน้าต่าง GUI ทั้งหมด
    รวมถึงการเก็บสถานะข้อมูลที่ต้องส่งผ่านระหว่างหน้าจอต่างๆ
    """
    def __init__(self, root):
        # 1. การตั้งค่าหน้าต่างหลัก (Main Window Setup)
        self.root = root
        self.root.title('DOMjudge Client') # กำหนดชื่อบนแถบหัวหน้าต่าง
        self.root.geometry('600x800')      # กำหนดขนาดเริ่มต้นของหน้าต่าง (กว้าง x สูง)
        self.root.resizable(True, True)    # อนุญาตให้ผู้ใช้งานย่อ/ขยายหน้าต่างได้ทั้งแกน X และ Y
        
        # 2. การกำหนดรูปแบบตัวอักษร (Typography & Styling)
        # ตั้งค่าฟอนต์มาตรฐานไว้เป็นตัวแปร เพื่อให้เรียกใช้ซ้ำได้ง่ายและเป็นระเบียบ
        self.font_header = ('Segoe UI', 18, 'bold')     # ฟอนต์สำหรับหัวเรื่องหลัก
        self.font_card_title = ('Segoe UI', 12, 'bold') # ฟอนต์สำหรับชื่อการแข่งขัน/ชื่อโจทย์บนการ์ด
        self.font_card_sub = ('Segoe UI', 10)           # ฟอนต์สำหรับข้อมูลรอง
        self.font_big_digit = ('Segoe UI', 36, 'bold')  # ฟอนต์ขนาดใหญ่พิเศษสำหรับหน้าแสดงสถิติตัวเลข
        
        # 3. การเตรียมตัวแปรสถานะ (State Management)
        # สร้างตัวแปรว่างไว้เพื่อเก็บข้อมูลระหว่างที่โปรแกรมกำลังทำงาน
        self.current_problem_data = None    # เก็บข้อมูลโจทย์ที่กำลังเปิดดูสถิติ
        self.current_team_list_mode = None  # เก็บโหมดว่ากำลังดูทีมที่ 'ส่งแล้ว' หรือ 'ยังไม่ส่ง'
        self.current_student_data = None    # เก็บข้อมูลของนักศึกษา/ทีมที่กำลังเลือกดูประวัติ
        self.selected_contest_id = None     # เก็บรหัสการแข่งขัน (Contest ID) ที่กำลังใช้งานอยู่
        self.current_display_data = []      # เก็บรายการข้อมูลที่กำลังวาดแสดงผลบนหน้าจอ
        
        # 4. การสร้างแผ่นกระดาน (Frames) สำหรับแต่ละหน้าจอ
        # สร้าง Frame เตรียมไว้สำหรับทุกหน้าต่าง (เปรียบเสมือนกระดาษใสที่วางซ้อนกันอยู่)
        self.frame_home = tk.Frame(root)
        self.frame_login = tk.Frame(root)
        self.frame_confirm = tk.Frame(root)
        self.frame_list = tk.Frame(root)
        self.frame_detail = tk.Frame(root)
        self.frame_stat = tk.Frame(root)
        self.frame_team_list = tk.Frame(root)
        self.frame_history = tk.Frame(root)
        self.frame_download = tk.Frame(root)
        self.frame_mode_select = tk.Frame(root)
        self.frame_ast_result = tk.Frame(root)
        
        # 5. การเริ่มต้นวาดองค์ประกอบลงในแต่ละหน้าจอ (UI Initialization)
        # เรียกใช้ฟังก์ชันย่อยเพื่อสร้าง ปุ่ม, ข้อความ, ช่องกรอกข้อมูล ใส่ลงไปในแต่ละ Frame ที่สร้างไว้ด้านบน
        self.init_home_frame()
        self.init_login_frame()
        self.init_confirm_frame()
        self.init_list_frame()
        self.init_detail_frame()
        self.init_stat_frame()
        self.init_team_list_frame()
        self.init_history_frame()
        self.init_download_frame()
        self.init_mode_select_frame()
        self.init_ast_result_frame()
        
        # 6. สั่งให้แสดงหน้าจอหลัก (Home) เป็นหน้าแรกเมื่อเปิดโปรแกรม
        self.show_frame(self.frame_home)

    def ui(self, func, *args, **kwargs):
        """
        ฟังก์ชันตัวกลางสำหรับจัดการระบบคิว (Thread-Safe UI Update)
        ใช้สำหรับรับคำสั่งจากเธรดเบื้องหลัง (Background Thread) ให้มาอัปเดตหน้าจอในเธรดหลัก (Main Thread)
        เพื่อป้องกันปัญหาโปรแกรมค้างหรือแครชเวลาโหลดข้อมูล
        """
        # root.after(0, ...) หมายถึงให้รันคำสั่งนี้ทันทีที่เธรดหลักว่าง
        self.root.after(0, lambda: func(*args, **kwargs))

    def show_frame(self, frame):
        """
        ฟังก์ชันสำหรับสลับหน้าจอ (Frame Switching)
        ทำงานโดยการซ่อนหน้าจอทั้งหมดที่มีอยู่ แล้วค่อยแสดงเฉพาะหน้าจอที่ต้องการ
        """
        # รวบรวมหน้าจอทั้งหมดไว้ในลิสต์
        frames = [
            self.frame_home, self.frame_login, self.frame_confirm,
            self.frame_list, self.frame_detail,
            self.frame_stat, self.frame_team_list, self.frame_history,
            self.frame_download, self.frame_mode_select, self.frame_ast_result
        ]
        # วนลูปใช้ pack_forget() เพื่อซ่อนทุกหน้าจอออกจากหน้าต่างหลัก
        for f in frames:
            f.pack_forget()
            
        # นำหน้าจอเป้าหมาย (frame) มาจัดวาง (pack) ลงในหน้าต่างหลัก
        # fill='both', expand=True ทำให้หน้าจอขยายเต็มพื้นที่ที่เหลืออยู่
        frame.pack(fill='both', expand=True, padx=20, pady=20)

  
    def init_home_frame(self):
        """
        ฟังก์ชันสำหรับสร้างองค์ประกอบในหน้าจอแรกสุด (Home / Splash Screen)
        """
        # สร้างตัวอักษรหัวเรื่องขนาดใหญ่ (DOMJUDGE) สีน้ำเงิน
        tk.Label(self.frame_home, text='DOMJUDGE', font=('Segoe UI', 28, 'bold'), fg='#1976D2').pack(pady=(150, 10))
        # สร้างคำบรรยายรอง
        tk.Label(self.frame_home, text='Similarity Detection System', font=('Segoe UI', 16), fg='#555555').pack(pady=(0, 60))
        
        # สร้างปุ่ม START สีเขียว เมื่อกดแล้วจะเรียกใช้ฟังก์ชันสลับหน้าจอไปยังหน้า Login
        self.btn_start = tk.Button(self.frame_home, text='START', bg='#4CAF50', fg='white', font=('Segoe UI', 14, 'bold'), width=15, height=2, command=lambda: self.show_frame(self.frame_login))
        self.btn_start.pack(pady=20)    

    def auto_fetch_and_open(self, target_page_func):
        """
        ฟังก์ชันสำหรับดึงข้อมูลการแข่งขันจากเซิร์ฟเวอร์แบบอัตโนมัติ (Background Task)
        มักถูกเรียกใช้เมื่อผู้ใช้งานกดเข้าหน้าจอที่ต้องใช้ข้อมูล แต่พบว่าในแคช (CACHE_DATA) ยังว่างเปล่า
        """
        # 1. เปลี่ยนสถานะบนหน้าจอเพื่อแจ้งให้ผู้ใช้งานรอ
        self.menu_status_label.config(text='Auto-fetching data Please wait', fg='blue')
        # ปิดการทำงานของปุ่มกดชั่วคราว เพื่อป้องกันการกดซ้ำซ้อนขณะกำลังโหลดข้อมูล
        self.btn_check.config(state='disabled')
        self.btn_dl.config(state='disabled')
        
        # 2. ฟังก์ชันย่อยสำหรับจัดการกรณี 'ดึงข้อมูลสำเร็จ'
        def on_auto_success(data):
            CACHE_DATA['contests'] = data # บันทึกข้อมูลที่ดึงมาลงในแคช
            # อัปเดต UI (ผ่านฟังก์ชัน self.ui เพื่อความปลอดภัยของเธรด)
            self.ui(self.lbl_total_contest.config, text=str(len(data))) # แสดงจำนวนรายการ
            self.ui(self.menu_status_label.config, text='Ready', fg='grey') # คืนสถานะกลับเป็นปกติ
            self.ui(self.btn_check.config, state='normal')
            self.ui(self.btn_dl.config, state='normal')
            self.ui(target_page_func) # เปิดหน้าจอเป้าหมายที่ตั้งใจจะเข้าตอนแรก
            
        # 3. ฟังก์ชันย่อยสำหรับจัดการกรณี 'เกิดข้อผิดพลาด'
        def on_auto_error(msg):
            self.ui(messagebox.showerror, 'Error', msg) # แสดงป๊อปอัปแจ้งเตือน
            self.ui(self.menu_status_label.config, text='Ready', fg='grey')
            self.ui(self.btn_check.config, state='normal')
            self.ui(self.btn_dl.config, state='normal')
            
        # 4. สร้างเธรดแยกเพื่อไปดึงข้อมูลเบื้องหลัง โดยไม่ทำให้หน้าจอโปรแกรมค้าง
        threading.Thread(daemon=True, target=process_check_data, args=(on_auto_success, on_auto_error)).start()

    def init_login_frame(self):
        """
        ฟังก์ชันสำหรับสร้างหน้าจอกรอกข้อมูลตั้งค่าการเชื่อมต่อ (Configuration / Login)
        """
        tk.Label(self.frame_login, text='Configuration', font=self.font_header).pack(pady=20)
        # สร้าง Frame ย่อยเพื่อใช้จัดกลุ่มช่องกรอกข้อมูลให้เป็นระเบียบ
        form = tk.Frame(self.frame_login)
        form.pack(pady=10)
        
        # สร้างช่องกรอกข้อมูล 3 แถว (URL, Username, Password) 
        # โดยมีค่าเริ่มต้น (Default value) ใส่ไว้ให้เพื่อความสะดวก
        self.create_input_row(form, 0, 'Base URL', config['BASE_URL'] or 'https://202.44.12.153')
        self.create_input_row(form, 1, 'Username', config['USERNAME'] or 'admin')
        self.create_input_row(form, 2, 'Password', config['PASSWORD'], is_password=True) # ซ่อนตัวอักษร
        
        # สร้างปุ่ม Next เพื่อไปหน้าตรวจสอบข้อมูล (Confirm)
        tk.Button(self.frame_login, text='Next', command=self.action_verify_input, width=15, bg='#E0E0E0').pack(pady=30)

    def create_input_row(self, parent, row, label, default_val, is_password=False):
        """
        ฟังก์ชันผู้ช่วย (Helper) สำหรับสร้างป้ายชื่อคู่กับช่องกรอกข้อความในแบบฟอร์ม
        """
        # สร้างป้ายชื่อ (Label) ชิดขวา (anchor='e')
        tk.Label(parent, text=label, anchor='e', width=10).grid(row=row, column=0, padx=5, pady=10)
        # สร้างช่องกรอกข้อความ (Entry)
        entry = tk.Entry(parent, width=35)
        # หากเป็นการกรอกรหัสผ่าน ให้ตั้งค่าเปลี่ยนตัวอักษรเป็นเครื่องหมาย *
        if is_password: entry.config(show='*')
        # ใส่ค่าเริ่มต้นลงไปในช่องกรอก
        entry.insert(0, default_val)
        entry.grid(row=row, column=1, padx=5, pady=10)
        
        # บันทึกวิดเจ็ตช่องกรอกลงในตัวแปรของคลาส เพื่อให้สามารถดึงข้อมูลไปใช้ในฟังก์ชันอื่นได้
        if label == 'Base URL': self.entry_url = entry
        elif label == 'Username': self.entry_user = entry
        elif label == 'Password': self.entry_pass = entry

    def action_verify_input(self):
        """
        ฟังก์ชันสำหรับตรวจสอบข้อมูลที่กรอกในหน้า Login ก่อนพาไปยังหน้า Confirm
        """
        # หากมีช่องใดช่องหนึ่งว่างเปล่า ให้แสดงแจ้งเตือนและหยุดการทำงาน
        if not self.entry_url.get() or not self.entry_user.get() or not self.entry_pass.get():
            messagebox.showwarning('Warning', 'All fields are required')
            return
            
        # นำข้อมูลที่กรอกในหน้า Login ไปแสดงผลสรุปบนหน้าจอ Confirm
        self.lbl_conf_url.config(text=self.entry_url.get())
        self.lbl_conf_user.config(text=self.entry_user.get())
        # สำหรับรหัสผ่าน ให้แปลงจำนวนตัวอักษรเป็นเครื่องหมาย * เพื่อความปลอดภัยบนหน้าจอ
        self.lbl_conf_pass.config(text='*' * len(self.entry_pass.get()))
        
        # เปลี่ยนหน้าจอไปยังหน้า Confirm
        self.show_frame(self.frame_confirm)

    def init_confirm_frame(self):
        """
        ฟังก์ชันสำหรับสร้างหน้าจอยืนยันข้อมูล (Confirm Details)
        ให้ผู้ใช้ตรวจทานข้อมูลเซิร์ฟเวอร์และบัญชีอีกครั้งก่อนบันทึกลงระบบ
        """
        tk.Label(self.frame_confirm, text='Confirm Details', font=self.font_header).pack(pady=20)
        # สร้างกล่อง (Frame) แบบมีกรอบ (relief='groove') เพื่อตีกรอบข้อมูลให้ดูเป็นสัดส่วน
        info_box = tk.Frame(self.frame_confirm, relief='groove', bd=2)
        info_box.pack(fill='x', padx=20, pady=20)
        
        # สร้างบรรทัดแสดงข้อมูล 3 แถว และจองตัวแปรไว้รอรับข้อมูลจากหน้า Login
        self.lbl_conf_url = self.create_info_row(info_box, 0, 'URL')
        self.lbl_conf_user = self.create_info_row(info_box, 1, 'User')
        self.lbl_conf_pass = self.create_info_row(info_box, 2, 'Pass')
        
        # สร้างกลุ่มปุ่มกด (ปุ่ม Back และปุ่ม Confirm สีเขียว)
        btn_box = tk.Frame(self.frame_confirm)
        btn_box.pack(pady=20)
        tk.Button(btn_box, text='Back', command=lambda: self.show_frame(self.frame_login), width=10).pack(side='left', padx=10)
        tk.Button(btn_box, text='Confirm', command=self.action_confirm, width=15, bg='#4CAF50', fg='white').pack(side='left', padx=10)

    def create_info_row(self, parent, row, label):
        """
        ฟังก์ชันผู้ช่วย (Helper) สำหรับสร้างบรรทัดแสดงข้อมูลสรุปในหน้า Confirm
        """
        # สร้างหัวข้อข้อมูล
        tk.Label(parent, text=label, font=('Segoe UI', 10, 'bold')).grid(row=row, column=0, sticky='e', padx=10, pady=8)
        # สร้างป้ายข้อความว่างๆ (สำหรับรอรับค่า)
        lbl = tk.Label(parent, text='', fg='#333')
        lbl.grid(row=row, column=1, sticky='w', padx=10, pady=8)
        # คืนค่าตัวออบเจกต์ Label กลับไปเพื่อให้โปรแกรมเอาไปปรับเปลี่ยนข้อความได้ทีหลัง
        return lbl

    def action_confirm(self):
        """
        ฟังก์ชันเมื่อผู้ใช้งานกดปุ่ม Confirm บนหน้าต่างยืนยันข้อมูล
        """
        # 1. บันทึกข้อมูลที่ผู้ใช้กรอกลงในตัวแปรตั้งค่า (config) ของระบบ 
        # ใช้ .strip() เพื่อตัดช่องว่าง (Space) หัวท้ายที่อาจเผลอพิมพ์ติดมา
        config['BASE_URL'] = self.entry_url.get().strip()
        config['USERNAME'] = self.entry_user.get().strip()
        config['PASSWORD'] = self.entry_pass.get().strip()
        
        # 2. สลับหน้าจอไปยังหน้ารายการแข่งขัน (List Frame) 
        self.show_frame(self.frame_list)
        # เปลี่ยนข้อความสรุปด้านบนให้แสดงสถานะกำลังโหลด
        self.lbl_dash_total.config(text='Loading data...')
        
        # 3. ล้างหน้าจอ: ทำลาย (destroy) ข้อมูลรายการเก่าทั้งหมดที่อาจเคยแสดงอยู่ในกรอบเลื่อนได้ (scroll_list_frame)
        for widget in self.scroll_list_frame.winfo_children(): widget.destroy()
        
        # แสดงป้ายข้อความชั่วคราวให้ผู้ใช้รู้ว่ากำลังดึงข้อมูลจากเซิร์ฟเวอร์
        tk.Label(self.scroll_list_frame, text='Fetching data from server, please wait...', bg='#f0f0f0').pack(pady=20)
        
        # 4. สร้างเธรดแยก (Background Thread) ไปเรียกใช้ฟังก์ชันดึงข้อมูล (process_check_data)
        # โดยส่งฟังก์ชัน on_success และ on_error ไปเป็นตัวรับผลลัพธ์
        threading.Thread(daemon=True, target=process_check_data, args=(self.on_success, self.on_error)).start()

    def run_check_data(self):
        """
        ฟังก์ชันสำหรับอัปเดตสถานะและเริ่มดึงข้อมูล (มักใช้ควบคู่กับโหมดอื่นที่ต้องรีเฟรชข้อมูล)
        """
        self.menu_status_label.config(text='Processing', fg='blue')
        threading.Thread(daemon=True, target=process_check_data, args=(self.on_success, self.on_error)).start()

    def on_success(self, data):
        """
        ฟังก์ชันนี้จะถูกเรียกเมื่อการดึงข้อมูลการแข่งขัน (process_check_data) ทำงาน 'สำเร็จ'
        """
        # อัปเดตข้อมูลที่ดึงมาลงในแคช
        CACHE_DATA['contests'] = data
        # เปลี่ยนป้ายข้อความแสดงจำนวนการแข่งขันทั้งหมดที่พบ
        self.lbl_dash_total.config(text=f'Total Contests: {len(data)}')
        # เรียกฟังก์ชันสำหรับ 'วาด' ข้อมูลลงบนหน้าจอให้ออกมาเป็นหน้าตาสวยงาม
        self.render_contest_list()

    def on_error(self, message):
        """
        ฟังก์ชันนี้จะถูกเรียกเมื่อการดึงข้อมูล 'ล้มเหลว' (เช่น รหัสผ่านผิด, เน็ตหลุด)
        """
        # ส่งคำสั่งผ่าน self.ui เพื่อเด้งป๊อปอัปแจ้งเตือนบนเธรดหลัก
        self.ui(messagebox.showerror, 'Error', message)
        # ส่งคำสั่งให้สลับหน้าจอกลับไปยังหน้า Login เพื่อให้ผู้ใช้งานแก้ไขข้อมูลใหม่
        self.ui(self.show_frame, self.frame_login)

    def init_list_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่าง 'เลือกการแข่งขัน' (Select Contest)
        """
        # สร้างป้ายหัวข้อ
        tk.Label(self.frame_list, text='Select Contest', font=self.font_header).pack(pady=10)
        # จองตัวแปรสำหรับแสดงจำนวนรายการทั้งหมด (จะถูกอัปเดตใน on_success)
        self.lbl_dash_total = tk.Label(self.frame_list, text='', fg='#1976D2', font=('Segoe UI', 10))
        self.lbl_dash_total.pack()
        
        # สร้างคอนเทนเนอร์หลัก
        container = tk.Frame(self.frame_list)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # --- เริ่มส่วนการสร้างระบบเลื่อนหน้าจอ (Scrollable Area) ---
        # 1. สร้าง Canvas เป็นฉากหลัง (เพราะ Canvas รองรับการเลื่อนได้ดีกว่า Frame ปกติ)
        self.canvas_list = tk.Canvas(container, bg='#f0f0f0', highlightthickness=0)
        # 2. สร้างแถบเลื่อน (Scrollbar) แนวตั้ง และผูกเข้ากับการเลื่อนแกน Y ของ Canvas
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.canvas_list.yview)
        # 3. สร้าง Frame ใส่ไว้ข้างใน Canvas (Frame นี้จะเป็นตัวรับกล่องข้อมูลจริงๆ)
        self.scroll_list_frame = tk.Frame(self.canvas_list, bg='#f0f0f0')
        
        # เมื่อ Frame ภายในมีการปรับขนาด (เพิ่ม/ลดข้อมูล) ให้คำนวณพื้นที่เลื่อนของ Canvas ใหม่ (Scrollregion)
        self.scroll_list_frame.bind('<Configure>', lambda e: self.canvas_list.configure(scrollregion=self.canvas_list.bbox('all')))
        # นำ Frame ไปแปะไว้บนพิกัด 0,0 ของ Canvas
        self.canvas_list.create_window((0, 0), window=self.scroll_list_frame, anchor='nw', width=420)
        # สั่งให้ Canvas รู้จักกับตัว Scrollbar 
        self.canvas_list.configure(yscrollcommand=scrollbar.set)
        
        self.canvas_list.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        # --- จบส่วนระบบเลื่อนหน้าจอ ---
        
        # สร้างปุ่ม Logout สีแดงไว้ด้านล่าง เพื่อย้อนกลับไปหน้าแรก (Home)
        btn_box = tk.Frame(self.frame_list)
        btn_box.pack(pady=10)
        tk.Button(btn_box, text='Logout', command=lambda: self.show_frame(self.frame_home), width=12, fg='red').pack(side='left', padx=10)

    def render_contest_list(self):
        """
        ฟังก์ชันสำหรับ 'วาด' ข้อมูลการแข่งขัน (ที่เก็บในแคช) ให้ออกมาเป็นกล่องข้อมูล (Card) บนหน้าจอ
        """
        self.show_frame(self.frame_list)
        # ล้างข้อมูลกล่องเดิม (หรือป้ายข้อความ Fetching data...) ออกจากหน้าจอ
        for widget in self.scroll_list_frame.winfo_children(): widget.destroy()
        
        contests = CACHE_DATA['contests']
        # กรณีดึงข้อมูลมาแล้วไม่พบการแข่งขันเลย
        if not contests:
            tk.Label(self.scroll_list_frame, text='No contests found', bg='#f0f0f0').pack(pady=20)
            return
            
        # วนลูปอ่านข้อมูลการแข่งขันทีละรายการ (c) พร้อมเก็บค่าดัชนี (index)
        for index, c in enumerate(contests):
            # 1. สร้างกล่องหลัก (Card) ให้นูนขึ้นมา (relief='raised') และเปลี่ยนเมาส์เป็นรูปมือคลิก (cursor='hand2')
            card = tk.Frame(self.scroll_list_frame, bg='white', relief='raised', bd=2, cursor='hand2')
            card.pack(fill='x', pady=8, padx=5)
            
            # 2. แถบสีด้านซ้าย (ตกแต่งให้ดูเป็นดีไซน์แบบ Card สมัยใหม่) สีฟ้า #2196F3
            strip = tk.Frame(card, bg='#2196F3', width=8)
            strip.pack(side='left', fill='y')
            
            # 3. พื้นที่สำหรับใส่ข้อความ
            content = tk.Frame(card, bg='white')
            content.pack(side='left', fill='both', expand=True, padx=10, pady=10)
            
            # ชื่อการแข่งขัน
            tk.Label(content, text=c['name'], bg='white', font=self.font_card_title, anchor='w').pack(fill='x')
            
            # แถวข้อมูลย่อย (เวลาที่เหลือ และ จำนวนโจทย์)
            info = tk.Frame(content, bg='white')
            info.pack(fill='x', pady=(5,0))
            
            time_txt = c['time_display']
            col = 'red' if time_txt=='Ended' else 'green' # ถ้าหมดเวลาให้โชว์สีแดง ถ้ายังให้โชว์สีเขียว
            
            tk.Label(info, text=time_txt, bg='white', fg=col, font=self.font_card_sub).pack(side='left')
            tk.Label(info, text=f'{c["problem_count"]} Problems', bg='white', fg='gray', font=self.font_card_sub).pack(side='right')
            
            # 4. การจัดการเมื่อผู้ใช้งาน 'คลิก' ที่การ์ด
            # สร้างฟังก์ชันจำลอง (lambda) ที่ผูกค่า index ปัจจุบันเอาไว้
            callback = lambda e, idx=index: self.on_contest_click(idx)
            card.bind('<Button-1>', callback) # <Button-1> หมายถึงคลิกเมาส์ซ้าย
            # สั่ง bind เผื่อให้ครอบคลุมถึงการเผลอคลิกโดนข้อความข้างในการ์ดด้วย
            for child in content.winfo_children(): child.bind('<Button-1>', callback)

    def on_contest_click(self, index):
        """
        ฟังก์ชันสำหรับจัดการเหตุการณ์เมื่อผู้ใช้คลิกเลือกการแข่งขัน (Contest) จากหน้ารายการ
        """
        # ดึงข้อมูลการแข่งขันจากแคชตาม index ที่ผู้ใช้คลิก
        data = CACHE_DATA.get('contests', [])[index]
        self.selected_contest_id = data['id'] # บันทึกรหัสการแข่งขันที่กำลังใช้งานอยู่
        
        # ตรวจสอบว่าเคยดึงรายละเอียดโจทย์ (problems_data) ของการแข่งขันนี้มาแล้วหรือยัง
        if data.get('problems_data') is None:
            # กรณีที่ยังไม่เคยดึงข้อมูล (Lazy Loading)
            # 1. เปลี่ยนหัวเรื่องเป็น Loading... 
            self.lbl_detail_header.config(text=f"Loading {data['name']}...")
            # 2. ล้างหน้าจอเดิมให้ว่างเปล่า
            for widget in self.scroll_prob_frame.winfo_children(): widget.destroy()
            # 3. สลับไปยังหน้าแสดงรายละเอียดโจทย์ (เพื่อโชว์สถานะโหลด)
            self.show_frame(self.frame_detail)
            # 4. สร้างเธรดแยกไปดึงข้อมูลเชิงลึก (โจทย์, ทีม, การส่งงาน) แบบเบื้องหลัง
            threading.Thread(daemon=True, target=self.fetch_single_contest_data, args=(data, index)).start()
        else:
            # กรณีที่เคยดึงข้อมูลมาแล้ว (ดึงมาจากแคชได้เลย)
            self.lbl_detail_header.config(text=data['name'])
            self.render_problem_cards(data) # วาดการ์ดโจทย์ขึ้นหน้าจอทันที
            self.show_frame(self.frame_detail)

    def fetch_single_contest_data(self, c_data, index):
        """
        ฟังก์ชันหลักสำหรับดึงข้อมูลเชิงลึกของการแข่งขัน (ทำงานบน Background Thread)
        ประกอบด้วย: ดึงรายชื่อโจทย์, ดึงรายชื่อทีม, และดึงข้อมูลการส่งคำตอบทั้งหมดมาจับคู่กัน
        """
        try:
            c_id = c_data['id']
            # 1. ดึงข้อมูล 3 ส่วนหลักจากเซิร์ฟเวอร์
            problems = fetch_data(f'/api/v4/contests/{c_id}/problems') or []
            submissions = fetch_data(f'/api/v4/contests/{c_id}/submissions') or []
            all_teams_data = fetch_data(f'/api/v4/contests/{c_id}/teams') or []
            
            # 2. สร้างพจนานุกรม (Dictionary) แมปปิ้ง รหัสทีม (team_id) เข้ากับ ชื่อทีม (team_name)
            team_id_to_name = {str(t['id']): t.get('name', str(t['id'])) for t in all_teams_data}
            all_team_ids = set(team_id_to_name.keys()) # เก็บ Set รหัสทีมทั้งหมดที่มีสิทธิ์เข้าแข่งขัน
            total_teams_count = len(all_team_ids)
            
            # 3. จัดกลุ่มการส่งคำตอบ (Submissions) ตามรายข้อ (Problem) และรายทีม (Team)
            submission_map = {}
            for s in submissions:
                p_id = str(s['problem_id'])
                t_id = str(s['team_id'])
                if p_id not in submission_map: submission_map[p_id] = {}
                if t_id not in submission_map[p_id]: submission_map[p_id][t_id] = []
                submission_map[p_id][t_id].append(s) # เก็บประวัติการส่งแต่ละครั้งเข้าไปในลิสต์
                
            problem_list_data = [] # ลิสต์เตรียมเก็บข้อมูลโจทย์ที่พร้อมนำไปแสดงผล
            
            # 4. วนลูปโจทย์แต่ละข้อ เพื่อสรุปสถิติว่า "ใครส่งแล้ว" และ "ใครยังไม่ส่ง"
            for p in problems:
                p_id = str(p['id'])
                teams_sent_data = []
                teams_notsent_data = []
                
                # ดึงประวัติการส่งคำตอบเฉพาะของโจทย์ข้อนี้มา
                submissions_for_problem = submission_map.get(p_id, {})
                sent_team_ids = set(submissions_for_problem.keys()) # หา Set รหัสทีมที่ส่งงานแล้ว
                notsent_team_ids = all_team_ids - sent_team_ids     # ใช้ Set Difference เพื่อหาทีมที่ยังขาดส่ง
                
                # 4.1 จัดการข้อมูล 'ทีมที่ส่งงานแล้ว'
                for tid in sent_team_ids:
                    # เรียงลำดับประวัติการส่งงานตามเวลา (Time)
                    history = sorted(submissions_for_problem[tid], key=lambda x: x.get('time', ''))
                    teams_sent_data.append({
                        'id': tid,
                        'name': team_id_to_name.get(tid, tid),
                        'count': len(history), # จำนวนครั้งที่ส่งแก้
                        'history': history     # เก็บไทม์ไลน์การส่งทั้งหมดไว้
                    })
                    
                # 4.2 จัดการข้อมูล 'ทีมที่ยังไม่ส่งงาน'
                for tid in notsent_team_ids:
                    teams_notsent_data.append({
                        'id': tid,
                        'name': team_id_to_name.get(tid, tid)
                    })
                    
                # เรียงรายชื่อทีมทั้งสองกลุ่มตามตัวอักษรเพื่อความสวยงาม
                teams_sent_data.sort(key=lambda x: x['name'])
                teams_notsent_data.sort(key=lambda x: x['name'])
                
                # 5. สรุปข้อมูลทั้งหมดของโจทย์ข้อนี้ลงใน Dictionary ย่อย
                problem_list_data.append({
                    'name': p.get('name', p_id),
                    'id': p_id,
                    'stats': {
                        'sent_count': len(teams_sent_data),
                        'notsent_count': len(teams_notsent_data),
                        'total': total_teams_count,
                        'data_sent': teams_sent_data,
                        'data_notsent': teams_notsent_data
                    }
                })
                
            # เรียงลำดับโจทย์ตาม ID เพื่อให้โจทย์ข้อแรกๆ (เช่น A, B, C) ขึ้นก่อน
            problem_list_data.sort(key=lambda x: x['id'])
            
            # 6. อัปเดตข้อมูลทั้งหมดกลับเข้าไปในตัวแปรแข่งขัน (c_data) และอัปเดตลงแคช
            c_data['problem_count'] = len(problems)
            c_data['problems_data'] = problem_list_data
            CACHE_DATA['contests'][index] = c_data
            
            # 7. ส่งคำสั่งให้เธรดหลัก (Main Thread) อัปเดตหน้าจอ
            self.ui(self.lbl_detail_header.config, text=c_data['name'])
            self.ui(self.render_problem_cards, c_data)
            
        except Exception as e:
            # กรณีดึงข้อมูลล้มเหลว
            self.ui(messagebox.showerror, 'Error', f'Failed to load contest details: {str(e)}')
            self.ui(self.show_frame, self.frame_list) # เด้งกลับไปหน้ารายชื่อการแข่งขัน

    def init_detail_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่างแสดงรายละเอียดโจทย์ (Problem Detail)
        """
        # ป้ายหัวเรื่องหลัก
        self.lbl_detail_header = tk.Label(self.frame_detail, text='Problems', font=self.font_header)
        self.lbl_detail_header.pack(pady=10)
        
        # --- เริ่มส่วนการสร้างระบบเลื่อนหน้าจอสำหรับรายการโจทย์ (Scrollable Canvas) ---
        container = tk.Frame(self.frame_detail)
        container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.canvas_prob = tk.Canvas(container, bg='#f0f0f0', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient='vertical', command=self.canvas_prob.yview)
        self.scroll_prob_frame = tk.Frame(self.canvas_prob, bg='#f0f0f0')
        self.scroll_prob_frame.bind('<Configure>', lambda e: self.canvas_prob.configure(scrollregion=self.canvas_prob.bbox('all')))
        self.canvas_prob.create_window((0, 0), window=self.scroll_prob_frame, anchor='nw', width=420)
        self.canvas_prob.configure(yscrollcommand=scrollbar.set)
        self.canvas_prob.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        # --- จบส่วนระบบเลื่อนหน้าจอ ---
        
        # สร้างคอนเทนเนอร์สำหรับกลุ่มปุ่มกดด้านล่าง
        btn_container = tk.Frame(self.frame_detail)
        btn_container.pack(pady=10)
        
        # ปุ่มสีเขียวสำหรับดาวน์โหลดโจทย์ทั้งหมดในการแข่งขันนี้
        self.btn_dl_all_detail = tk.Button(btn_container, text='Download All Problems', bg='#4CAF50', fg='white', font=('Segoe UI', 9, 'bold'), command=self.download_all_from_detail)
        self.btn_dl_all_detail.pack(side='left', padx=10)
        
        # ปุ่มย้อนกลับไปหน้ารายชื่อการแข่งขัน
        tk.Button(btn_container, text='Back to Contest List', command=self.render_contest_list).pack(side='left', padx=10)
        
        # ปุ่มสีส้มสำหรับรันการวิเคราะห์ AST (หาความเหมือนของโค้ด) รวดเดียวครบทุกข้อ และออกรายงานเป็น CSV
        self.btn_ast_all = tk.Button(btn_container, text='AST All Problems (CSV)', bg='#FFCC80', font=('Segoe UI', 9, 'bold'), command=self.start_ast_all_problems)
        self.btn_ast_all.pack(side='left', padx=10)
        
        # ป้ายสถานะสำหรับแจ้งเตือนตอนกำลังดาวน์โหลดไฟล์ (เช่น กำลังโหลด 1/10) สีน้ำเงิน
        self.lbl_detail_status = tk.Label(self.frame_detail, text='', fg='blue')
        self.lbl_detail_status.pack(pady=5)

    def render_problem_cards(self, contest_data):
        """
        ฟังก์ชันสำหรับ 'วาด' รายการโจทย์ให้ออกมาเป็นกล่องการ์ด (Card) บนหน้าจอ Detail Frame
        """
        # ล้างข้อมูลกล่องโจทย์เก่าที่อาจค้างอยู่ออกจากหน้าจอให้หมด
        for widget in self.scroll_prob_frame.winfo_children(): widget.destroy()
        
        # ดึงลิสต์ข้อมูลโจทย์ทั้งหมดออกมาจากการแข่งขันที่เลือก
        problems = contest_data.get('problems_data', [])
        
        # วนลูปสร้างการ์ดโจทย์ทีละข้อ
        for p in problems:
            # 1. สร้างกล่องหลัก (Card) ให้นูนขึ้นมา (relief='raised') และเปลี่ยนเมาส์เป็นรูปมือ
            card = tk.Frame(self.scroll_prob_frame, bg='white', relief='raised', bd=1, cursor='hand2')
            card.pack(fill='x', pady=6, padx=5)
            
            # 2. ป้ายชื่อโจทย์
            tk.Label(card, text=p['name'], bg='white', font=('Segoe UI', 11, 'bold')).pack(pady=5)
            
            # 3. ป้ายสรุปสถิติ (บอกว่ามีคนส่งกี่ทีม จากทีมทั้งหมด)
            tk.Label(card, text=f'Sent {p["stats"]["sent_count"]} / {p["stats"]["total"]}', bg='white').pack()
            
            # 4. เมื่อผู้ใช้งาน 'คลิก' ที่การ์ดโจทย์ ให้พาไปยังหน้าสถิติเชิงลึก (Stat Page)
            # ใช้ lambda เพื่อล็อกข้อมูลโจทย์ข้อนี้ (data=p) ส่งข้ามไปยังฟังก์ชัน go_to_stat_page
            card.bind('<Button-1>', lambda e, data=p: self.go_to_stat_page(data))

    def init_stat_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่างแสดงสถิติรายโจทย์ (Problem Statistics)
        เป็นหน้าแดชบอร์ดที่มีตัวเลขขนาดใหญ่ และปุ่มคำสั่งดาวน์โหลด/วิเคราะห์ AST
        """
        # 1. ส่วนหัวเรื่อง (จะถูกอัปเดตเป็นชื่อโจทย์ในภายหลัง)
        self.lbl_stat_title = tk.Label(self.frame_stat, text='Title', font=('Segoe UI', 16, 'bold'))
        self.lbl_stat_title.pack(pady=10)
        
        # 2. ส่วนแสดงตัวเลขสถิติ "ทีมที่ส่งงานแล้ว" (สีเขียว)
        self.lbl_stat_sent = tk.Label(self.frame_stat, text='0', font=self.font_big_digit, fg='green')
        self.lbl_stat_sent.pack()
        tk.Button(self.frame_stat, text='View Submitted Teams', command=lambda: self.go_to_team_list_page('sent')).pack(pady=5)
        
        # 3. ส่วนแสดงตัวเลขสถิติ "ทีมที่ยังไม่ส่งงาน" (สีแดง)
        self.lbl_stat_notsent = tk.Label(self.frame_stat, text='0', font=self.font_big_digit, fg='red')
        self.lbl_stat_notsent.pack()
        tk.Button(self.frame_stat, text='View Missing Teams', command=lambda: self.go_to_team_list_page('notsent')).pack(pady=5)
        
        # 4. ป้ายสถานะสำหรับแจ้งเตือนระบบ (สีน้ำเงิน) จะอยู่ด้านล่างสุด
        self.lbl_stat_dl_status = tk.Label(self.frame_stat, text='', fg='blue')
        self.lbl_stat_dl_status.pack(side='bottom', pady=10)
        
        # 5. กลุ่มปุ่มกดดำเนินการต่างๆ (Action Buttons) จัดไว้ด้านล่างหน้าจอ
        btn_action_frame = tk.Frame(self.frame_stat)
        btn_action_frame.pack(side='bottom', pady=30)
        
        # ปุ่มดาวน์โหลดไฟล์ซอร์สโค้ดเฉพาะโจทย์ข้อนี้ (สีฟ้าอ่อน)
        self.btn_dl_prob_stat = tk.Button(btn_action_frame, text='Download All Submission File', bg='#E3F2FD', font=('Segoe UI', 11, 'bold'), command=self.download_all_for_this_problem)
        self.btn_dl_prob_stat.pack(side='left', padx=10)
        
        # ปุ่มย้อนกลับไปหน้ารายชื่อโจทย์ (Detail Frame)
        tk.Button(btn_action_frame, text='Back', command=lambda: self.show_frame(self.frame_detail), width=10, font=('Segoe UI', 11)).pack(side='left', padx=10)
        
        # ปุ่มเข้าสู่โหมดวิเคราะห์ความคล้ายคลึง AST (สีเหลืองอ่อน)
        self.btn_go_mode_select = tk.Button(btn_action_frame, text='Go to AST Analysis', bg='#FFF9C4', font=('Segoe UI', 11, 'bold'), command=self.show_mode_select_page)
        self.btn_go_mode_select.pack(side='left', padx=10)

    def show_mode_select_page(self):
        """
        ฟังก์ชันสำหรับเตรียมข้อมูลก่อนเปลี่ยนไปหน้าเลือกโหมดวิเคราะห์ AST
        ทำหน้าที่ดึงรายชื่อ 'ทีมที่ส่งงานแล้ว' มาใส่ในตัวเลือก (Combobox)
        """
        sent_teams = self.current_problem_data['stats']['data_sent']
        
        # นำรหัสและชื่อทีมมาต่อกัน แล้วยัดใส่ลิสต์เพื่อใช้เป็นตัวเลือกให้ผู้ใช้
        self.combo_source_team['values'] = [f'{t["id"]}  {t["name"]}' for t in sent_teams]
        
        # ถ้ามีคนส่งงาน ให้โชว์ตัวเลือกแรกเป็นค่าตั้งต้น แต่ถ้าไม่มีให้โชว์ช่องว่าง
        if sent_teams: self.combo_source_team.current(0)
        else: self.combo_source_team.set('')
        
        # สลับหน้าจอไปยังหน้าเลือกโหมด (Mode Select Frame)
        self.show_frame(self.frame_mode_select)

    def init_mode_select_frame(self):
        """
        ฟังก์ชันสร้างหน้าจอ 'เลือกโหมดการวิเคราะห์' (Analysis Mode)
        แบ่งเป็น 2 โหมดหลัก คือ Single Reference (1 เทียบทั้งหมด) และ Matrix (ทุกคนเทียบกันเอง)
        """
        tk.Label(self.frame_mode_select, text='Analysis Mode', font=self.font_header).pack(pady=20)
        
        # --- 1. โหมด Single Reference ---
        # สร้างกรอบสำหรับโหมดเปรียบเทียบแบบใช้โค้ด 1 ทีมเป็นตัวตั้ง
        frame_single = tk.Frame(self.frame_mode_select, relief='groove', bd=2)
        frame_single.pack(fill='x', padx=20, pady=10)
        tk.Label(frame_single, text='Single Reference Mode', font=('Segoe UI', 12, 'bold')).pack(pady=(10, 5))
        tk.Label(frame_single, text='Select Source Team', font=('Segoe UI', 10)).pack()
        
        # กล่องเลือกทีม (Combobox) ที่เตรียมข้อมูลไว้จากฟังก์ชัน show_mode_select_page
        self.combo_source_team = ttk.Combobox(frame_single, state='readonly', width=40)
        self.combo_source_team.pack(pady=5)
        
        # ปุ่มสำหรับรันโหมด Single
        self.btn_run_single = tk.Button(frame_single, text='Run Single Mode', bg='#E3F2FD', width=20, height=2, font=('Segoe UI', 11, 'bold'), command=self.run_single_mode)
        self.btn_run_single.pack(pady=(5, 15))
        
        # --- 2. โหมด Matrix (All vs All) ---
        # สร้างกรอบสำหรับโหมดเปรียบเทียบทุกคนเข้าด้วยกัน
        frame_matrix = tk.Frame(self.frame_mode_select, relief='groove', bd=2)
        frame_matrix.pack(fill='x', padx=20, pady=10)
        tk.Label(frame_matrix, text='All vs All Matrix Mode', font=('Segoe UI', 12, 'bold')).pack(pady=(10, 5))
        tk.Label(frame_matrix, text='Compare everyone and save CSV', fg='gray').pack()
        
        # ปุ่มสำหรับรันโหมด Matrix
        self.btn_run_matrix = tk.Button(frame_matrix, text='Run Matrix Mode', bg='#E8F5E9', width=20, height=2, font=('Segoe UI', 11, 'bold'), command=self.run_matrix_mode)
        self.btn_run_matrix.pack(pady=(5, 15))
        
        # ป้ายแจ้งสถานะการทำงาน (เช่น 'กำลังตรวจสอบ...')
        self.lbl_mode_status = tk.Label(self.frame_mode_select, text='Ready', fg='#1976D2', font=('Segoe UI', 10))
        self.lbl_mode_status.pack(pady=10)
        
        # ปุ่มย้อนกลับหน้าสถิติ
        tk.Button(self.frame_mode_select, text='Back to Stat', command=lambda: self.show_frame(self.frame_stat)).pack(side='bottom', pady=20)

    def run_single_mode(self):
        """
        ฟังก์ชันสำหรับเริ่มกระบวนการตรวจสอบเมื่อผู้ใช้กดปุ่ม 'Run Single Mode'
        """
        idx = self.combo_source_team.current()
        # ตรวจสอบว่าผู้ใช้ได้เลือกทีมต้นทางแล้วหรือยัง
        if idx < 0:
            messagebox.showwarning('Warning', 'กรุณาเลือก Source Team ก่อน')
            return
            
        # ดึงข้อมูลรหัสการแข่งขัน, รหัสโจทย์, และชื่อโจทย์
        c_id = self.selected_contest_id
        p_id = self.current_problem_data['id']
        p_name = self.current_problem_data['name']
        
        # ดึงข้อมูลทีมต้นทางจากลำดับ Index ที่ผู้ใช้เลือกจาก Combobox
        source_team = self.current_problem_data['stats']['data_sent'][idx]
        source_team_id = source_team['id']
        
        # ล็อกปุ่มกดทั้งสองโหมดเพื่อป้องกันการกดซ้ำซ้อนขณะประมวลผล
        self.btn_run_single.config(state='disabled')
        self.btn_run_matrix.config(state='disabled')
        self.lbl_mode_status.config(text='กำลังตรวจแบบ Single Reference', fg='blue')
        
        # สร้างเธรดแยกเพื่อไปรันการวิเคราะห์ AST แบบเบื้องหลัง (ป้องกันหน้าจอค้าง)
        threading.Thread(daemon=True, target=self.thread_ast_analysis, args=(c_id, p_id, p_name, source_team_id)).start()

    def run_matrix_mode(self):
        """
        ฟังก์ชันสำหรับเตรียมความพร้อมและสั่งเริ่มการวิเคราะห์ความคล้ายคลึงแบบ All vs All (Matrix Mode)
        """
        # 1. ดึงข้อมูลพื้นฐานที่จำเป็นต้องใช้ในการวิเคราะห์จากตัวแปรสถานะ
        c_id = self.selected_contest_id
        p_id = self.current_problem_data['id']
        p_name = self.current_problem_data['name']
        
        # 2. ปิดการใช้งาน (Disable) ปุ่มกดรันโหมดทั้งสอง เพื่อป้องกันผู้ใช้กดซ้ำขณะที่ระบบกำลังประมวลผล
        self.btn_run_single.config(state='disabled')
        self.btn_run_matrix.config(state='disabled')
        
        # 3. อัปเดตป้ายสถานะให้ผู้ใช้ทราบว่าระบบกำลังทำอะไรอยู่
        self.lbl_mode_status.config(text='กำลังดึงข้อมูลสำหรับโหมด Matrix', fg='blue')
        
        # 4. สร้างและเริ่มการทำงานของเธรดแยก (Background Thread) เพื่อไม่ให้หน้าต่างโปรแกรมค้าง
        # โดยส่งเป้าหมายไปที่ฟังก์ชัน thread_matrix_analysis พร้อมแนบพารามิเตอร์ที่จำเป็นไปด้วย
        threading.Thread(daemon=True, target=self.thread_matrix_analysis, args=(c_id, p_id, p_name)).start()

    def go_to_stat_page(self, problem_data):
        """
        ฟังก์ชันสำหรับอัปเดตข้อมูลและสลับหน้าจอไปยังหน้า 'สถิติของโจทย์' (Stat Page)
        """
        # บันทึกข้อมูลโจทย์ข้อที่เลือกลงในตัวแปรคลาส เพื่อให้ฟังก์ชันอื่นอ้างอิงได้
        self.current_problem_data = problem_data
        
        # อัปเดตข้อความบนป้าย (Label) ต่างๆ ให้ตรงกับข้อมูลโจทย์ข้อปัจจุบัน
        self.lbl_stat_title.config(text=problem_data['name'])
        self.lbl_stat_sent.config(text=str(problem_data['stats']['sent_count']))
        self.lbl_stat_notsent.config(text=str(problem_data['stats']['notsent_count']))
        
        # สลับหน้าจอให้แสดงผลหน้าสถิติ
        self.show_frame(self.frame_stat)

    def init_team_list_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่างแสดง 'รายชื่อทีม' (Team List)
        """
        # สร้างป้ายหัวข้อของหน้าจอ
        self.lbl_team_list_header = tk.Label(self.frame_team_list, text='Team List', font=('Segoe UI', 16, 'bold'))
        self.lbl_team_list_header.pack(pady=10)
        
        # สร้างกล่องรายการ (Listbox) สำหรับแสดงชื่อทีมทั้งหมด
        self.listbox_teams = tk.Listbox(self.frame_team_list, font=('Segoe UI', 12))
        self.listbox_teams.pack(fill='both', expand=True, padx=20)
        
        # ผูกเหตุการณ์ (Event Binding): เมื่อดับเบิลคลิกเมาส์ซ้าย (<Double-1>) ที่รายชื่อใน Listbox 
        # ให้เรียกใช้ฟังก์ชัน show_student_history_page เพื่อดูประวัติการส่งงาน
        self.listbox_teams.bind('<Double-1>', self.show_student_history_page)
        
        # สร้างปุ่มย้อนกลับไปยังหน้าสถิติ (Stat Page)
        tk.Button(self.frame_team_list, text='Back', command=lambda: self.show_frame(self.frame_stat)).pack(pady=20)

    def go_to_team_list_page(self, mode):
        """
        ฟังก์ชันสำหรับจัดเตรียมข้อมูลและสลับไปยังหน้ารายชื่อทีม
        รับพารามิเตอร์ mode เพื่อแยกว่าจะให้แสดงทีมที่ 'sent' (ส่งแล้ว) หรือ 'notsent' (ขาดส่ง)
        """
        # บันทึกโหมดปัจจุบันไว้ เพื่อให้ฟังก์ชันอื่นรู้บริบทการทำงาน
        self.current_team_list_mode = mode
        
        # ล้างข้อมูลรายชื่อทีมเก่าที่อาจค้างอยู่ใน Listbox ออกให้หมด
        self.listbox_teams.delete(0, tk.END)
        problem_name = self.current_problem_data['name']
        
        # ปรับเปลี่ยนข้อความหัวเรื่องให้สอดคล้องกับโจทย์และโหมดที่เลือก
        if mode == 'sent': self.lbl_team_list_header.config(text=f"Submitted Teams - {problem_name}")
        else: self.lbl_team_list_header.config(text=f"Missing Teams - {problem_name}")
            
        # เลือกดึงชุดข้อมูลรายชื่อทีมจาก stats ตามโหมดที่ระบุ
        data = self.current_problem_data['stats']['data_sent'] if mode == 'sent' else self.current_problem_data['stats']['data_notsent']
        self.current_display_data = data # บันทึกข้อมูลที่กำลังแสดงผลไว้ใช้อ้างอิงตอนถูกคลิก
        
        # วนลูปนำชื่อทีมแต่ละทีมแทรกลงไปใน Listbox
        for item in data:
            self.listbox_teams.insert(tk.END, item['name'])
            
        # สลับหน้าจอให้แสดงผลหน้ารายชื่อทีม
        self.show_frame(self.frame_team_list)

    def init_history_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่างแสดง 'ประวัติการส่งงานของนักศึกษา' (History)
        """
        # สร้างป้ายหัวข้อของหน้าจอ
        self.lbl_history_header = tk.Label(self.frame_history, text='History', font=('Segoe UI', 16, 'bold'))
        self.lbl_history_header.pack(pady=10)
        
        # สร้าง Frame สำหรับรองรับปุ่มประวัติการส่งงานแต่ละครั้ง
        self.scroll_hist_frame = tk.Frame(self.frame_history)
        self.scroll_hist_frame.pack(fill='both', expand=True)
        
        # สร้าง Frame ย่อยเพื่อจัดกลุ่มปุ่มกดดำเนินการต่างๆ ไว้ด้วยกัน
        btn_frame = tk.Frame(self.frame_history)
        btn_frame.pack(pady=10)
        
        # ปุ่มสำหรับดาวน์โหลดไฟล์ซอร์สโค้ดทุกเวอร์ชันที่นักศึกษาคนนี้เคยส่งมา
        self.btn_dl_team_hist = tk.Button(btn_frame, text='Download All Submissions', bg='#4CAF50', fg='white', font=('Segoe UI', 11, 'bold'), command=self.download_all_team_history)
        self.btn_dl_team_hist.pack(side='left', padx=10)
        
        # ปุ่มย้อนกลับไปยังหน้ารายชื่อทีม
        tk.Button(btn_frame, text='Back', command=lambda: self.show_frame(self.frame_team_list)).pack(side='left', padx=10)
        
        # ป้ายสำหรับแสดงสถานะการดาวน์โหลด (อัปเดตเป็นเปอร์เซ็นต์หรือข้อความแจ้งเตือน)
        self.lbl_hist_dl_status = tk.Label(self.frame_history, text='', fg='blue')
        self.lbl_hist_dl_status.pack(pady=5)

    def show_student_history_page(self, event):
        """
        ฟังก์ชันจัดการเหตุการณ์เมื่อดับเบิลคลิกเลือกรายชื่อทีม 
        เพื่อนำประวัติการส่งโค้ดทั้งหมดมาแสดงเป็นปุ่มให้คลิกดาวน์โหลดได้ทีละตัว
        """
        # หากโหมดปัจจุบันไม่ใช่ทีมที่ส่งงานแล้ว (เช่น กดมาจากทีมที่ขาดส่ง) จะไม่มีประวัติให้ดู ให้หยุดทำงานทันที
        if self.current_team_list_mode != 'sent': return
        
        # ดึงลำดับ (Index) ของทีมที่ถูกเลือกใน Listbox
        selection = self.listbox_teams.curselection()
        if not selection: return # หากไม่ได้เลือกอะไรเลยให้หยุดทำงาน
        
        idx = selection[0]
        # ดึงข้อมูลของทีมนั้นๆ จากตัวแปรอ้างอิง
        student = self.current_display_data[idx]
        self.current_student_data = student 
        
        # อัปเดตหัวเรื่องเป็นชื่อของนักศึกษา/ทีมนั้นๆ
        self.lbl_history_header.config(text=f'History {student["name"]}')
        
        # ล้างปุ่มประวัติการส่งเก่าๆ ออกจากหน้าจอก่อน
        for w in self.scroll_hist_frame.winfo_children(): w.destroy()
        
        # วนลูปอ่านประวัติการส่งงานทีละรอบของนักศึกษาคนนี้
        for sub in student['history']:
            # สร้างปุ่มสำหรับแต่ละครั้งที่ส่ง โดยแสดง รหัสการส่ง (Sub ID) และ เวลา (ผ่านการฟอร์แมตแล้ว)
            btn = tk.Button(self.scroll_hist_frame, text=f'Sub {sub["id"]} at {format_timestamp(sub.get("time"))}',
                            # ใช้ lambda s=sub เพื่อล็อกตัวแปรข้อมูลการส่งชุดนี้ไว้ ผูกกับฟังก์ชันดาวน์โหลดไฟล์เดี่ยว
                            command=lambda s=sub: self.download_single_file(s))
            btn.pack(fill='x', pady=2) # วางเรียงปุ่มจากบนลงล่าง
            
        # ล้างสถานะแจ้งเตือนการดาวน์โหลดให้เป็นค่าว่าง
        self.lbl_hist_dl_status.config(text='') 
        
        # สลับหน้าจอมายังหน้าประวัติการส่งงาน
        self.show_frame(self.frame_history)

    def download_single_file(self, submission_data):
        """
        ฟังก์ชันสำหรับเตรียมการดาวน์โหลดไฟล์ซอร์สโค้ดของการส่งคำตอบ 1 รายการ
        """
        # ดึงรหัสการส่งงาน (Submission ID)
        sub_id = submission_data['id']
        # สร้าง URL สำหรับเรียก API เพื่อดึงซอร์สโค้ดของรหัสการส่งนี้
        url = f'/api/v4/contests/{self.selected_contest_id}/submissions/{sub_id}/source-code'
        # สร้างเธรดเบื้องหลัง (Background Thread) เพื่อไปดาวน์โหลดข้อมูล ป้องกันไม่ให้หน้าจอโปรแกรมค้าง
        threading.Thread(daemon=True, target=self.thread_download_single, args=(url, sub_id)).start()

    def thread_download_single(self, url, sub_id):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง เพื่อดาวน์โหลดข้อมูลและถอดรหัสไฟล์กลับมาเป็นข้อความปกติ
        """
        # ดึงข้อมูลจากเซิร์ฟเวอร์
        data = fetch_data(url)
        if data:
            # ข้อมูลซอร์สโค้ดจะถูกส่งมาในรูปแบบลิสต์ ให้ดึงข้อมูลไฟล์ตัวแรกมา
            file_info = data[0]
            # โค้ดที่ได้มาจะถูกเข้ารหัสเป็น Base64 เพื่อการส่งผ่านเครือข่าย ต้องถอดรหัส (Decode) กลับเป็นไบนารี
            decoded = base64.b64decode(file_info['source'])
            # ส่งคำสั่งกลับไปที่เธรดหลัก (Main Thread) เพื่อให้เปิดหน้าต่างบันทึกไฟล์ (Save Dialog) อย่างปลอดภัย
            self.root.after(0, lambda: self.save_dialog(file_info['filename'], decoded))

    def save_dialog(self, default_name, content):
        """
        ฟังก์ชันสำหรับเปิดหน้าต่างให้ผู้ใช้งานเลือกตำแหน่งและตั้งชื่อไฟล์เพื่อบันทึกลงเครื่อง
        """
        # เปิดหน้าต่างโต้ตอบ (Save As) โดยกำหนดชื่อไฟล์เริ่มต้น (initialfile) ให้ตรงกับชื่อดั้งเดิม
        path = filedialog.asksaveasfilename(initialfile=default_name)
        # ถ้าผู้ใช้งานระบุตำแหน่งและกด Save (ไม่กดยกเลิก)
        if path:
            # เปิดไฟล์ในโหมด 'wb' (Write Binary) เพื่อเขียนข้อมูลไบนารีที่ถอดรหัสแล้วลงไป
            with open(path, 'wb') as f: f.write(content)
            # แสดงหน้าต่างป๊อปอัปแจ้งเตือนว่าบันทึกสำเร็จ
            messagebox.showinfo('Success', 'File saved')

    def init_download_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่าง 'ดาวน์โหลดแบบกำหนดเอง' (Selective Download)
        เพื่อรองรับการดาวน์โหลดทีละหลายๆ ข้อ (Bulk Download)
        """
        # ป้ายหัวเรื่องหลักของหน้าจอ
        tk.Label(self.frame_download, text='Selective Download', font=self.font_header).pack(pady=10)
        
        # --- ขั้นตอนที่ 1: เลือกการแข่งขัน (Contest) ---
        tk.Label(self.frame_download, text='1 Select Contest', font=('Segoe UI', 10, 'bold')).pack(pady=(10, 5))
        # สร้าง Combobox (ดรอปดาวน์) แบบอ่านอย่างเดียว เพื่อให้ผู้ใช้คลิกเลือก
        self.combo_contest = ttk.Combobox(self.frame_download, state='readonly', width=45)
        self.combo_contest.pack()
        # ผูกเหตุการณ์: เมื่อผู้ใช้เลือกการแข่งขันเสร็จ ให้ไปเรียกฟังก์ชัน on_download_contest_select ทันที
        self.combo_contest.bind('<<ComboboxSelected>>', self.on_download_contest_select)
        
        # --- ขั้นตอนที่ 2: เลือกโจทย์ปัญหา (Problems) ---
        tk.Label(self.frame_download, text='2 Select Problems', font=('Segoe UI', 10, 'bold')).pack(pady=(15, 5))
        frame_listbox = tk.Frame(self.frame_download)
        frame_listbox.pack()
        # สร้างแถบเลื่อน (Scrollbar) เผื่อกรณีที่โจทย์มีจำนวนเยอะ
        scrollbar = ttk.Scrollbar(frame_listbox, orient='vertical')
        
        # สร้าง Listbox แบบ MULTIPLE เพื่อให้ผู้ใช้งานสามารถคลิกเลือกโจทย์ได้ "มากกว่า 1 ข้อ"
        self.listbox_dl_problems = tk.Listbox(frame_listbox, selectmode=tk.MULTIPLE, width=45, height=10, yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.listbox_dl_problems.yview)
        self.listbox_dl_problems.pack(side='left', fill='both')
        scrollbar.pack(side='right', fill='y')
        
        # --- ขั้นตอนที่ 3: เลือกโฟลเดอร์ปลายทาง (Destination Folder) ---
        tk.Label(self.frame_download, text='3 Select Destination Folder', font=('Segoe UI', 10, 'bold')).pack(pady=(15, 5))
        # ป้ายแสดงเส้นทางโฟลเดอร์ปัจจุบันที่เลือก
        self.lbl_dl_folder = tk.Label(self.frame_download, text='Folder: Not Selected', fg='gray', font=('Segoe UI', 9))
        self.lbl_dl_folder.pack(pady=(0, 5))
        # ปุ่ม Browse เพื่อเรียกหน้าต่างเลือกโฟลเดอร์ระบบปฏิบัติการ
        tk.Button(self.frame_download, text='Browse...', command=self.select_download_folder).pack(pady=(0, 15))
        
        # --- ปุ่มเริ่มดำเนินการ ---
        # ปุ่มสีเขียว: สั่งดาวน์โหลดเฉพาะโจทย์ที่ 'ถูกคลิกไฮไลท์' ไว้ใน Listbox เท่านั้น
        self.btn_start_dl = tk.Button(self.frame_download, text='Start Download', bg='green', fg='white', font=('Segoe UI', 11, 'bold'), command=self.start_bulk_download)
        self.btn_start_dl.pack(pady=20)
        # ปุ่มสีส้ม: ทางลัด สั่งดาวน์โหลดโจทย์ 'ทั้งหมด' ของการแข่งขันนี้รวดเดียว
        self.btn_dl_all = tk.Button(self.frame_download, text='Download All Problems', bg='#FF9800', fg='white', font=('Segoe UI', 11, 'bold'), command=self.start_download_all)
        self.btn_dl_all.pack(pady=(0, 20))
        
        # ป้ายแจ้งสถานะการทำงานแบบ Real-time (เช่น Ready, Downloading...)
        self.lbl_dl_status = tk.Label(self.frame_download, text='Ready', fg='#1976D2', font=('Segoe UI', 10))
        self.lbl_dl_status.pack()

    def select_download_folder(self):
        """
        ฟังก์ชันเปิดหน้าต่างให้ผู้ใช้เลือก 'โฟลเดอร์ปลายทาง' (Directory) เพื่อจัดเก็บไฟล์
        """
        # เปิดหน้าต่างให้เลือกโฟลเดอร์
        path = filedialog.askdirectory(title='Select Destination Folder')
        if path: # หากผู้ใช้เลือกโฟลเดอร์สำเร็จ
            self.download_folder = path # บันทึกเส้นทาง (Path) ไว้ในตัวแปรคลาส
            # อัปเดตป้ายข้อความบนหน้าจอให้โชว์เส้นทางที่เพิ่งเลือกมา
            self.lbl_dl_folder.config(text=f'Folder: {self.download_folder}')

    def open_download_page(self):
        """
        ฟังก์ชันเตรียมข้อมูลและเคลียร์หน้าจอก่อนจะสลับมาเปิดหน้าดาวน์โหลด
        """
        # ตรวจสอบว่าในแคชมีข้อมูลการแข่งขันมาหรือยัง
        if not CACHE_DATA.get('contests'):
            # ถ้ายังไม่มี ให้สั่งไปดึงข้อมูลใหม่เบื้องหลังก่อน แล้วค่อยกลับมารันฟังก์ชันเปิดหน้านี้ซ้ำ
            self.auto_fetch_and_open(self.open_download_page)
            return
            
        # เอาข้อมูลรหัสและชื่อการแข่งขัน ยัดเข้าไปใน Combobox เพื่อสร้างเป็นตัวเลือก
        self.combo_contest['values'] = [f'{c["id"]}  {c["name"]}' for c in CACHE_DATA['contests']]
        # ล้างรายชื่อโจทย์เก่าที่อาจค้างอยู่ใน Listbox
        self.listbox_dl_problems.delete(0, tk.END)
        # รีเซ็ตสถานะกลับเป็น Ready
        self.lbl_dl_status.config(text='Ready')
        # สลับหน้าจอมาให้ผู้ใช้งานเห็นอย่างเป็นทางการ
        self.show_frame(self.frame_download)

    def on_download_contest_select(self, event):
        """
        ฟังก์ชันที่จะทำงานอัตโนมัติเมื่อผู้ใช้ 'เลือกการแข่งขัน' ใน Combobox 
        เพื่อดึงรายชื่อโจทย์ของการแข่งขันนั้นมาโชว์ใน Listbox (ขั้นตอนที่ 2)
        """
        # ดึงลำดับ (Index) ที่ผู้ใช้กดเลือก
        idx = self.combo_contest.current()
        if idx < 0: return # ถ้ายังไม่ได้เลือกให้หยุดทำงาน
        
        # ล้าง Listbox เผื่อมีรายชื่อโจทย์ของการแข่งขันเก่าค้างอยู่
        self.listbox_dl_problems.delete(0, tk.END)
        # ดึงข้อมูลการแข่งขันจากแคชตาม Index ที่เลือก
        contest = CACHE_DATA['contests'][idx]
        
        # ตรวจสอบว่าในแคชมีการดึงข้อมูล 'รายชื่อโจทย์' มาเก็บไว้หรือยัง
        if contest.get('problems_data') is None:
            # ถ้ายังไม่มี: เปลี่ยนป้ายสถานะเป็น Loading...
            self.lbl_dl_status.config(text='Loading problems...')
            # สั่งสร้างเธรดแยก (Background) ไปดึงรายชื่อโจทย์จาก API (เพื่อไม่ให้จอค้าง)
            threading.Thread(daemon=True, target=self.fetch_problems_only, args=(contest, idx)).start()
        else:
            # ถ้ามีข้อมูลโจทย์ในแคชอยู่แล้ว: ให้นำข้อมูลมาแสดงบน Listbox ได้เลยทันที
            self.show_problems_in_listbox(contest)

    def fetch_problems_only(self, contest, index):
        """
        ฟังก์ชันสำหรับดึงข้อมูล 'รายชื่อโจทย์' (Problems) จากเซิร์ฟเวอร์แบบเบาๆ (Lightweight)
        ทำงานอยู่บนเธรดเบื้องหลัง (Background Thread) เพื่อเตรียมข้อมูลให้หน้าดาวน์โหลด
        """
        c_id = contest['id']
        # ดึงข้อมูลจาก API หากเชื่อมต่อล้มเหลว หรือไม่มีข้อมูล ให้ใช้ลิสต์ว่าง [] แทนเพื่อป้องกัน Error
        problems = fetch_data(f'/api/v4/contests/{c_id}/problems') or []
        
        # ใช้ List Comprehension เพื่อคัดกรองเฉพาะฟิลด์ที่จำเป็น (id และ name) ลดขนาดข้อมูลในหน่วยความจำ
        # p.get('name', str(p['id'])) หมายถึงถ้าโจทย์ข้อไหนไม่มีชื่อ ให้เอารหัสโจทย์มาใช้เป็นชื่อแทน
        prob_data = [{'id': str(p['id']), 'name': p.get('name', str(p['id']))} for p in problems]
        
        # อัปเดตข้อมูลโจทย์ที่จัดรูปแบบแล้วกลับเข้าไปในตัวแปร contest และเซฟลงแคช
        contest['problems_data'] = prob_data
        CACHE_DATA['contests'][index] = contest
        
        # ส่งคำสั่งให้เธรดหลัก (Main Thread) วาดรายชื่อโจทย์ลงบน Listbox
        self.ui(self.show_problems_in_listbox, contest)
        # ส่งคำสั่งให้เธรดหลัก เปลี่ยนป้ายสถานะกลับเป็น 'Ready' เพื่อแจ้งว่าดึงข้อมูลเสร็จแล้ว
        self.ui(self.lbl_dl_status.config, text='Ready')  
        
    def show_problems_in_listbox(self, contest):
        """
        ฟังก์ชันสำหรับนำรายชื่อโจทย์ที่อยู่ในแคช มาแสดงผลให้ผู้ใช้งานคลิกเลือกบน Listbox
        """
        # ล้างข้อมูลเดิมใน Listbox ออกให้หมดก่อน
        self.listbox_dl_problems.delete(0, tk.END)
        # วนลูปอ่านข้อมูลโจทย์ทีละข้อ
        for p in contest['problems_data']:
            # นำรหัสโจทย์และชื่อโจทย์มาต่อกัน แล้วแทรกลงไปในบรรทัดสุดท้าย (tk.END) ของ Listbox
            self.listbox_dl_problems.insert(tk.END, f'{p["id"]}  {p["name"]}')          

    def start_bulk_download(self):
        """
        ฟังก์ชันเมื่อผู้ใช้กดปุ่ม 'Start Download' (ปุ่มสีเขียว)
        ทำหน้าที่ตรวจสอบความถูกต้องของข้อมูลที่เลือก ก่อนส่งไปดาวน์โหลดจริง
        """
        # 1. ตรวจสอบว่าได้เลือกการแข่งขันใน Combobox หรือยัง
        c_idx = self.combo_contest.current()
        if c_idx < 0:
            messagebox.showwarning('Warning', 'Please select a contest first')
            return
            
        # 2. ตรวจสอบว่าได้ไฮไลท์เลือกโจทย์ใน Listbox หรือยัง (เลือกได้หลายข้อ)
        selected_indices = self.listbox_dl_problems.curselection()
        if not selected_indices:
            # ถ้ายังไม่ได้คลิกเลือกโจทย์เลย ให้แจ้งเตือนและหยุดการทำงาน
            messagebox.showwarning('Warning', 'Please select at least one problem')
            return
            
        # 3. เตรียมข้อมูล
        contest = CACHE_DATA['contests'][c_idx]
        # แปลงลำดับ Index ที่ผู้ใช้คลิกเลือก ให้กลายเป็น 'รหัสโจทย์' (Problem ID) ที่ต้องใช้ดึงข้อมูล
        selected_problem_ids = [contest['problems_data'][i]['id'] for i in selected_indices]
        
        # 4. ปิดการใช้งานปุ่มดาวน์โหลด (Disable) ชั่วคราว เพื่อป้องกันการกดปุ่มเบิ้ล (Double Submit)
        self.btn_start_dl.config(state='disabled')
        # 5. สั่งเริ่มการดาวน์โหลดผ่านเธรดเบื้องหลัง โดยส่งรหัสโจทย์ที่ถูกเลือกไปด้วย
        threading.Thread(daemon=True, target=self.thread_bulk_download, args=(contest, selected_problem_ids)).start()

    def start_download_all(self):
        """
        ฟังก์ชันเมื่อผู้ใช้กดปุ่ม 'Download All Problems' (ปุ่มสีส้ม)
        เป็นทางลัดสำหรับดาวน์โหลดทุกข้อโดยไม่ต้องไปนั่งคลิกไฮไลท์เลือกใน Listbox
        """
        # 1. ตรวจสอบว่าได้เลือกการแข่งขันหรือยัง
        c_idx = self.combo_contest.current()
        if c_idx < 0:
            messagebox.showwarning('Warning', 'Please select a contest first')
            return
            
        # 2. ดึงข้อมูลการแข่งขันจากแคช
        contest = CACHE_DATA['contests'][c_idx]
        # ดึง 'รหัสโจทย์ทั้งหมด' ที่อยู่ในการแข่งขันนี้ออกมาใส่ลิสต์ทันที โดยไม่สนว่าผู้ใช้ไฮไลท์อะไรไว้
        selected_problem_ids = [p['id'] for p in contest['problems_data']]
        
        # 3. ล็อกปุ่มดาวน์โหลดทั้ง 2 ปุ่ม ป้องกันการสั่งงานซ้ำซ้อน
        self.btn_start_dl.config(state='disabled')
        self.btn_dl_all.config(state='disabled')
        
        # 4. สั่งเริ่มการดาวน์โหลดผ่านเธรดเบื้องหลัง แบบเหมาหมดทุกข้อ
        threading.Thread(daemon=True, target=self.thread_bulk_download, args=(contest, selected_problem_ids)).start()

    def thread_bulk_download(self, contest, selected_problem_ids):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง (Background Thread) สำหรับการดาวน์โหลดไฟล์ซอร์สโค้ดแบบกลุ่ม (Bulk Download)
        รับพารามิเตอร์เป็นการแข่งขัน (contest) และรหัสโจทย์ที่ต้องการดาวน์โหลด (selected_problem_ids)
        """
        # 1. ตรวจสอบความพร้อมของโฟลเดอร์ปลายทาง
        # หากผู้ใช้ยังไม่ได้เลือกโฟลเดอร์ปลายทาง (download_folder) ให้แจ้งเตือนและปลดล็อกปุ่มกด
        if not hasattr(self, 'download_folder') or not self.download_folder:
            self.ui(messagebox.showwarning, 'Warning', 'Please select a destination folder')
            self.ui(self.btn_start_dl.config, state='normal')
            self.ui(self.btn_dl_all.config, state='normal')
            return
            
        root_dir = self.download_folder
        # หากโฟลเดอร์ที่ระบุไม่มีอยู่จริง ให้สร้างขึ้นมาใหม่ (รวมถึงสร้างโฟลเดอร์ย่อยหากจำเป็น)
        if not os.path.exists(root_dir): os.makedirs(root_dir)
        
        c_id = contest['id']
        c_name = contest['name']
        
        # 2. แจ้งสถานะกำลังเตรียมข้อมูล
        self.ui(self.lbl_dl_status.config, text=f'Fetching submission list for {c_name}')
        
        # ดึงประวัติการส่งงานทั้งหมดของการแข่งขันนี้ (เพื่อเอามาจับคู่กับโจทย์ที่เลือก)
        subs = fetch_data(f'/api/v4/contests/{c_id}/submissions')
        if not subs:
            # หากไม่มีใครเคยส่งงานเลยในการแข่งขันนี้
            self.ui(self.lbl_dl_status.config, text='No submissions found')
            self.ui(self.btn_start_dl.config, state='normal')
            return
            
        # 3. คัดกรองเฉพาะการส่งงาน (Submissions) ที่ตรงกับรหัสโจทย์ที่ผู้ใช้เลือกมา (List Comprehension)
        subs_to_download = [s for s in subs if str(s.get('problem_id')) in selected_problem_ids]
        total_subs = len(subs_to_download)
        
        # หากโจทย์ที่เลือกมา ไม่มีใครเคยส่งงานเลย
        if total_subs == 0:
            self.ui(self.lbl_dl_status.config, text='No submissions match selection')
            self.ui(self.btn_start_dl.config, state='normal')
            return
            
        success_count = 0 # ตัวนับจำนวนไฟล์ที่ดาวน์โหลดสำเร็จ
        
        # 4. เริ่มกระบวนการดาวน์โหลดและบันทึกไฟล์ทีละรายการ
        for i, s in enumerate(subs_to_download):
            # อัปเดตสถานะบนหน้าจอ (เช่น Downloading 1 / 10)
            self.ui(self.lbl_dl_status.config, text=f'Downloading {i+1} / {total_subs}')
            
            # เรียก API ดึงข้อมูลไฟล์ซอร์สโค้ดของการส่งครั้งนี้
            src = fetch_data(f'/api/v4/contests/{c_id}/submissions/{s["id"]}/source-code')
            if src:
                # สร้างเส้นทางโฟลเดอร์แบบจัดหมวดหมู่: Root / รหัสการแข่งขัน / รหัสโจทย์ / รหัสทีม
                path = os.path.join(root_dir, str(c_id), str(s['problem_id']), str(s['team_id']))
                # สร้างโฟลเดอร์ตามเส้นทางที่กำหนด หากยังไม่มีอยู่จริง
                if not os.path.exists(path): os.makedirs(path)
                
                # ตั้งชื่อไฟล์โดยนำ รหัสการส่ง (Submission ID) มานำหน้าชื่อไฟล์เดิม เพื่อป้องกันชื่อซ้ำ
                filename = f'{s["id"]}_{src[0]["filename"]}'
                try:
                    # เปิดไฟล์ในโหมด 'wb' (Write Binary)
                    with open(os.path.join(path, filename), 'wb') as f:
                        # ถอดรหัส (Decode) ข้อมูล Base64 กลับเป็นโค้ดปกติ และเขียนลงไฟล์
                        f.write(base64.b64decode(src[0]['source']))
                    success_count += 1
                except: pass # หากเขียนไฟล์ไม่ได้ (เช่น ติด Permission) ให้ข้ามไปข้อถัดไป
                
            # หน่วงเวลา 0.1 วินาที เพื่อไม่ให้ส่ง Request ถี่เกินไปจนเซิร์ฟเวอร์แบน (Rate Limiting)
            time.sleep(0.1) 
            
        # 5. สิ้นสุดกระบวนการ แจ้งเตือนความสำเร็จ และปลดล็อกปุ่มกด
        self.ui(self.lbl_dl_status.config, text=f'Done! {success_count}/{total_subs} files.')
        self.ui(messagebox.showinfo, 'Success', f'Downloaded {success_count} files')
        self.ui(self.btn_start_dl.config, state='normal')
        self.ui(self.btn_dl_all.config, state='normal')

    def prepare_records_for_problem(self, contest_id, problem_id):
        """
        ฟังก์ชันสำหรับเตรียมข้อมูล 'รหัสต้นฉบับล่าสุด' ของแต่ละทีมในโจทย์ที่เลือก 
        เพื่อนำไปเข้าสู่กระบวนการวิเคราะห์ความคล้ายคลึง (AST Analysis)
        """
        # 1. ค้นหาข้อมูลการแข่งขันและข้อมูลโจทย์จากแคช (CACHE_DATA)
        contest_data = next((c for c in CACHE_DATA['contests'] if str(c['id']) == str(contest_id)), None)
        if not contest_data or not contest_data.get('problems_data'): return None
            
        problem_data = next((p for p in contest_data['problems_data'] if str(p['id']) == str(problem_id)), None)
        if not problem_data: return None
            
        latest_subs = {} # ดิกชันนารีสำหรับเก็บการส่งงาน 'ครั้งล่าสุด' ของแต่ละทีม
        
        # 2. คัดกรองเฉพาะการส่งงานครั้งล่าสุด (Latest Submission)
        for team_stat in problem_data['stats']['data_sent']:
            t_id = team_stat['id']
            if team_stat['history']:
                # ดึงตัวสุดท้ายของ history (ซึ่งเรียงตามเวลามาแล้ว)
                latest_subs[t_id] = team_stat['history'][-1]
                # แนบชื่อทีมติดไปด้วยเพื่อใช้แสดงผลในตาราง
                latest_subs[t_id]['team_name'] = team_stat['name']
                
        # หากมีทีมที่ส่งงานน้อยกว่า 2 ทีม จะไม่สามารถเปรียบเทียบความคล้ายคลึงกันได้
        if len(latest_subs) < 2: return None
        
        records = [] # ลิสต์เก็บโครงสร้างต้นไม้ที่แปลงสมบูรณ์แล้วของแต่ละทีม
        total_teams = len(latest_subs)
        
        # 3. เข้าสู่กระบวนการดาวน์โหลดและวิเคราะห์โค้ดทีละทีม
        for count, (t_id, sub) in enumerate(latest_subs.items()):
            # อัปเดตสถานะบนหน้าจอทุกๆ 5 ทีม เพื่อลดภาระการอัปเดต GUI ที่บ่อยเกินไป
            if (count + 1) % 5 == 0 or count == 0:
                self.ui(self.lbl_mode_status.config, text=f'Parsing code {count+1}/{total_teams}')
                
            # ดึงไฟล์ซอร์สโค้ดจากเซิร์ฟเวอร์
            src_data = fetch_data(f'/api/v4/contests/{contest_id}/submissions/{sub["id"]}/source-code')
            time.sleep(0.1) # หน่วงเวลาเล็กน้อยเพื่อป้องกันเซิร์ฟเวอร์แบน
            
            if src_data and src_data[0].get('source'):
                try:
                    # 3.1 ถอดรหัส Base64 ให้เป็นข้อความปกติ (ละเว้นอักขระที่อ่านไม่ได้ด้วย errors='ignore')
                    decoded_code = base64.b64decode(src_data[0]['source']).decode('utf-8', errors='ignore')
                    
                    # 3.2 สร้างต้นไม้ AST จากโค้ดที่ทำความสะอาดแล้ว
                    ast_node = parse_c_code(clean_source(decoded_code))
                    if not ast_node: continue # ถ้าแปลผลไม่ได้ (Syntax Error) ให้ข้ามทีมนี้ไป
                    
                    # 3.3 ทำการขัดเกลา AST ให้กระชับขึ้น (Optimization Pipeline)
                    remover = UnusedVariableRemover(ast_node) # ลบตัวแปรที่ไม่ใช้
                    inliner = FunctionInliner(ast_node)       # นำเนื้อหาฟังก์ชันย่อยมาต่อกัน (Inline)
                    ast_node = inliner.inline(ast_node)       # รัน inliner
                    sort_commutative_ops(ast_node)            # จัดเรียงตัวดำเนินการคณิตศาสตร์ให้เป็นแบบแผน
                    
                    # 3.4 แปลง AST ให้เป็นโครงสร้างสำหรับ ZSS และลบชื่อตัวแปรจริง (Anonymization)
                    id_map = build_id_map(ast_node)
                    tree = ast_to_tree(ast_node, id_map)
                    
                    # แก้ไขโครงสร้างในกรณีที่ tree มีหลายกิ่งระดับเดียวกัน
                    if isinstance(tree, list): tree = ('Root', tree)
                        
                    # 3.5 รวบรวมข้อมูลทั้งหมดที่พร้อมวิเคราะห์เก็บลงลิสต์
                    records.append({
                        'team_id': t_id,
                        'team_name': sub.get('team_name', f'Team {t_id}'),
                        'repr': normalize_ast_repr(ast_node), # ข้อความ AST สตริงมาตรฐาน (ไม่มีชื่อตัวแปร ไม่มีเว้นวรรค)
                        'tree': tree_to_zss(tree),            # โครงสร้างต้นไม้ ZSS สำหรับเทียบระยะห่าง (TED)
                        'features': extract_features(ast_node), # สถิติลักษณะเฉพาะของโค้ด (เช่น จำนวน If, For, ค่าคงที่)
                        'node_count': sum(extract_features(ast_node).values()) # รวมจำนวนโหนดทั้งหมดเพื่อใช้วัดขนาดโค้ด
                    })
                except: continue # หากเกิดข้อผิดพลาดในการประมวลผลโค้ดทีมใด ให้ข้ามไปทีมต่อไปเลย
                
        # ส่งคืนลิสต์ข้อมูลของทุกทีมที่พร้อมนำไปเข้าสมการ ZSS แล้ว
        return records


    def thread_ast_analysis(self, contest_id, problem_id, problem_name, source_team_id):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง สำหรับการเปรียบเทียบโค้ดแบบ Single Reference
        (นำทีมที่ต้องสงสัย 1 ทีม ไปเปรียบเทียบกับทีมที่เหลือทั้งหมดในโจทย์ข้อเดียวกัน)
        """
        try:
            # 1. เรียกใช้ฟังก์ชันเตรียมข้อมูล (ดึงโค้ด, แปลง AST, ทำ ZSS) ของทุกทีม
            records = self.prepare_records_for_problem(contest_id, problem_id)
            # หากมีผู้ส่งน้อยกว่า 2 ทีม จะไม่สามารถเปรียบเทียบได้ ให้แจ้งเตือนและหยุดทำงาน
            if not records:
                self.ui(self.lbl_mode_status.config, text='Insufficient Data', fg='red')
                self.ui(self.btn_run_single.config, state='normal')
                self.ui(self.btn_run_matrix.config, state='normal')
                return
                
            # 2. ค้นหา 'ข้อมูลของทีมต้นทาง' (Source Record) จากรายการทั้งหมด
            source_record = next((r for r in records if str(r['team_id']) == str(source_team_id)), None)
            if not source_record:
                self.ui(self.lbl_mode_status.config, text='Source code not found', fg='red')
                self.ui(self.btn_run_single.config, state='normal')
                self.ui(self.btn_run_matrix.config, state='normal')
                return
                
            total_pairs = len(records) - 1 # จำนวนคู่ที่ต้องเปรียบเทียบ (ไม่นับตัวเอง)
            results = []                   # ลิสต์เก็บผลลัพธ์คะแนนความเหมือน
            current_pair = 0
            A = source_record              # ให้ A เป็นทีมเป้าหมาย (ตัวตั้ง)
            
            # 3. วนลูปนำทีม A ไปเปรียบเทียบกับทีม B (ทีมอื่นๆ ทั้งหมด)
            for B in records:
                # ข้ามการเปรียบเทียบกับตัวเอง
                if str(B['team_id']) == str(source_team_id): continue
                
                current_pair += 1
                # อัปเดตสถานะบนหน้าจอทุกๆ 5 คู่ เพื่อลดภาระ GUI
                if current_pair % 5 == 0 or current_pair == 1:
                    self.ui(self.lbl_mode_status.config, text=f'Comparing {current_pair}/{total_pairs}')
                time.sleep(0.001) # หน่วงเวลาเล็กน้อยให้หน้าจอหลักได้หายใจ
                
                # 4. กระบวนการคำนวณความเหมือน
                # ตรวจสอบเบื้องต้นว่าโครงสร้างข้อความ (String Repr) เหมือนกันเป๊ะ 100% หรือไม่
                same_repr = (A['repr'] == B['repr'])
                
                # ใช้ไลบรารี ZSS คำนวณ 'ระยะห่างการแก้ไข' (Tree Edit Distance) ระหว่างต้นไม้ 2 ต้น
                # ยิ่งค่าน้อย แปลว่าต้นไม้หน้าตาเหมือนกันมาก
                dist = simple_distance(A['tree'], B['tree'])
                
                # หาจำนวนโหนด (ความยาวโค้ด) ของทีมที่เขียนยาวกว่ามาเป็นฐานในการคำนวณ
                max_nodes = max(A['node_count'], B['node_count'])
                
                # แปลงค่าระยะห่าง (Distance) ให้กลายเป็นเปอร์เซ็นต์ความเหมือน (Similarity Score)
                # สูตร: 1.0 - (ระยะห่าง / จำนวนโหนดมากสุด)
                sim = max(0.0, 1.0 - (dist / max_nodes)) if max_nodes > 0 else 1.0
                
                # 5. สร้างคำอธิบาย (Explainability) 
                # หากความคล้ายคลึงเกิน 70% หรือโครงสร้างเหมือนกันเป๊ะ ให้ระบบหาเหตุผลประกอบ
                reason = explain_similarity(A['team_name'], A['features'], B['team_name'], B['features']) if sim >= 0.7 or same_repr else 'Different Structure'
                
                # เก็บผลลัพธ์ลงในลิสต์ (แปลงคะแนนจากทศนิยมเป็นเปอร์เซ็นต์ x100)
                results.append({'teamA': A['team_name'], 'teamB': B['team_name'], 'sim_pct': sim * 100, 'reason': reason})
                
            # 6. เรียงลำดับผลลัพธ์จากทีมที่โค้ด "เหมือนกันมากที่สุด" ไว้บนสุด
            results.sort(key=lambda x: x['sim_pct'], reverse=True)
            
            # 7. สิ้นสุดการทำงาน อัปเดตสถานะ ปลดล็อกปุ่ม และส่งข้อมูลไปแสดงผล/บันทึกไฟล์
            self.ui(self.lbl_mode_status.config, text='Analysis Complete', fg='green')
            self.ui(self.btn_run_single.config, state='normal')
            self.ui(self.btn_run_matrix.config, state='normal')
            self.ui(self.render_ast_results, results, problem_name)      # โชว์ผลลัพธ์บนหน้าจอ
            self.ui(self.save_single_csv_dialog, results, problem_name)  # เปิดหน้าต่างให้เซฟเป็นไฟล์ .csv
            
        except Exception:
            # หากระบบล่มกลางคัน ให้แจ้ง Error และปลดล็อกปุ่มกด
            self.ui(self.lbl_mode_status.config, text='Error Processing Data', fg='red')
            self.ui(self.btn_run_single.config, state='normal')
            self.ui(self.btn_run_matrix.config, state='normal')

    def thread_matrix_analysis(self, contest_id, problem_id, problem_name):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง สำหรับการสร้างตารางเมทริกซ์ความคล้ายคลึง (All vs All)
        (นำทุกคนที่ส่งงานมาเปรียบเทียบไขว้กันเองทั้งหมด เพื่อหาเครือข่ายการคัดลอก)[cite: 1]
        """
        try:
            # 1. เตรียมข้อมูล AST ของทุกทีม
            records = self.prepare_records_for_problem(contest_id, problem_id)
            if not records:
                self.ui(self.lbl_mode_status.config, text='Insufficient Data', fg='red')
                self.ui(self.btn_run_single.config, state='normal')
                self.ui(self.btn_run_matrix.config, state='normal')
                return
                
            # 2. เตรียมโครงสร้างตารางเมทริกซ์ (Dictionary 2 มิติ)
            teams_list = [r['team_name'] for r in records]
            # สร้างตารางเปล่าที่มีค่าเริ่มต้น 0.0 โดยให้แกน X และ Y เป็นชื่อทีม
            matrix = {t: {t2: 0.0 for t2 in teams_list} for t in teams_list}
            
            total_checks = len(records) * len(records) # จำนวนคู่ที่ต้องคำนวณทั้งหมด
            current_check = 0
            
            # 3. วนลูปแบบไขว้ (Nested Loop) ให้ทีม A เทียบกับทีม B ทุกคน
            for A in records:
                for B in records:
                    current_check += 1
                    # อัปเดตสถานะความคืบหน้าบนหน้าจอ
                    if current_check % 20 == 0 or current_check == 1:
                        self.ui(self.lbl_mode_status.config, text=f'Calculating Matrix {current_check}/{total_checks}')
                    time.sleep(0.001)
                    
                    # 4. การคำนวณความเหมือน
                    # หากเป็นทีมเดียวกัน (A เทียบ A) ไม่ต้องคำนวณ ให้ได้ 100% ไปเลย
                    if A['team_id'] == B['team_id']:
                        matrix[A['team_name']][B['team_name']] = 100.0
                        continue
                        
                    # คำนวณ Tree Edit Distance ของทีม A และ B
                    dist = simple_distance(A['tree'], B['tree'])
                    max_nodes = max(A['node_count'], B['node_count'])
                    
                    # แปลงระยะห่างเป็นเปอร์เซ็นต์ความคล้ายคลึง
                    sim = max(0.0, 1.0 - (dist / max_nodes)) if max_nodes > 0 else 1.0
                    
                    # บันทึกคะแนน (0-100) ลงในช่องตารางเมทริกซ์ที่ตัดกันระหว่าง A และ B[cite: 1]
                    matrix[A['team_name']][B['team_name']] = sim * 100
                    
            # 5. สิ้นสุดการคำนวณ ส่งข้อมูลเมทริกซ์ทั้งหมดไปสร้างเป็นไฟล์ CSV[cite: 1]
            self.ui(self.save_csv_dialog, matrix, teams_list, problem_name)
            
        except Exception:
            self.ui(self.lbl_mode_status.config, text='Matrix Error', fg='red')
            self.ui(self.btn_run_single.config, state='normal')
            self.ui(self.btn_run_matrix.config, state='normal')

    def save_csv_dialog(self, matrix, team_names, problem_name):
        """
        ฟังก์ชันสำหรับเปิดหน้าต่างให้ผู้ใช้เลือกที่เซฟไฟล์ผลลัพธ์ (ตารางเมทริกซ์แบบ All vs All) ออกเป็นไฟล์ .csv
        """
        # เปิดหน้าต่าง Save As โดยกำหนดชื่อไฟล์เริ่มต้นให้อัตโนมัติ (เช่น matrix_Problem1.csv)
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile=f'matrix_{problem_name}.csv')
        if path:
            # เปิดไฟล์เพื่อเขียนข้อมูล ('w') โดยใช้ encoding='utf-8-sig' เพื่อให้รองรับภาษาไทยใน Microsoft Excel ได้อย่างสมบูรณ์แบบ
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # เขียนแถวแรก (Header) เป็นคำว่า 'Team' ตามด้วยรายชื่อทีมทั้งหมดเรียงกันไปทางขวา
                writer.writerow(['Team'] + team_names)
                
                # วนลูปเพื่อเขียนข้อมูลตารางคะแนนทีละบรรทัด
                for t1 in team_names:
                    # คอลัมน์แรกสุดของแต่ละบรรทัดคือ ชื่อทีมที่เป็นตัวตั้งต้น
                    row = [t1]
                    # วนลูปดึงคะแนนที่ t1 เทียบกับ t2 (ทีมอื่นๆ) แล้วใส่ลงในช่องตาราง โดยปัดทศนิยมให้เหลือ 2 ตำแหน่ง
                    for t2 in team_names: row.append(f'{matrix[t1][t2]:.2f}')
                    # เขียนบรรทัดนี้ลงไฟล์ CSV
                    writer.writerow(row)
                    
            # แจ้งเตือนเมื่อเขียนไฟล์เสร็จ
            messagebox.showinfo('Success', 'File successfully saved.')
            
        # ไม่ว่าจะเซฟสำเร็จ หรือผู้ใช้กดยกเลิก (Cancel) ก็ให้ปลดล็อกปุ่มกดทั้งหมดให้กลับมาใช้งานได้ปกติ
        self.btn_run_matrix.config(state='normal')
        self.btn_run_single.config(state='normal')
        self.lbl_mode_status.config(text='Ready')

    def save_single_csv_dialog(self, results, problem_name):
        """
        ฟังก์ชันสำหรับเปิดหน้าต่างให้ผู้ใช้เลือกที่เซฟไฟล์ผลลัพธ์ (แบบ Single Reference) ออกเป็นไฟล์ .csv
        """
        path = filedialog.asksaveasfilename(defaultextension='.csv', initialfile=f'single_report_{problem_name}.csv')
        if path:
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                # เขียนหัวตาราง (Header) ซึ่งแตกต่างจากโหมด Matrix เพราะเน้นบอกเหตุผลประกอบด้วย
                writer.writerow(['Rank', 'Source Team', 'Compare Team', 'Similarity (%)', 'Reason'])
                
                # วนลูปเขียนผลลัพธ์ทีละคู่ (ซึ่งถูกจัดเรียงตามเปอร์เซ็นต์ความเหมือนมาแล้ว)
                for idx, res in enumerate(results):
                    writer.writerow([idx + 1, res['teamA'], res['teamB'], f"{res['sim_pct']:.2f}", res['reason']])
                    
            messagebox.showinfo('Success', 'CSV file saved.')

    def start_ast_all_problems(self):
        """
        ฟังก์ชันสำหรับสั่งวิเคราะห์ AST และสร้างตาราง Matrix ของ "โจทย์ทุกข้อ" ในการแข่งขันแบบรวดเดียว
        เป็นทางลัดสำหรับอาจารย์ที่ต้องการตรวจสอบการทุจริตแบบเหมาทั้งการแข่งขัน
        """
        # 1. ตรวจสอบข้อมูลก่อนเริ่มทำงาน
        c_id = self.selected_contest_id
        if not c_id:
            messagebox.showwarning('Warning', 'Please select a contest first')
            return
            
        # ค้นหาข้อมูลการแข่งขันปัจจุบันจากแคช
        contest = next((c for c in CACHE_DATA['contests'] if str(c['id']) == str(c_id)), None)
        if not contest: return
            
        # 2. เปิดหน้าต่างให้เลือก "โฟลเดอร์หลัก" ที่ต้องการจะให้โปรแกรมเซฟไฟล์ CSV จำนวนมากลงไป
        folder_path = filedialog.askdirectory(title='Select Folder to Save AST Reports')
        if not folder_path: return # ถ้าผู้ใช้กดยกเลิก ให้หยุดทำงาน
            
        # 3. ล็อกปุ่มกดเพื่อป้องกันการสั่งงานซ้ำซ้อน
        self.btn_ast_all.config(state='disabled')
        # 4. สร้างเธรดเบื้องหลัง (Background Thread) ไปประมวลผลข้อมูลหนัก เพื่อไม่ให้หน้าจอหลักค้าง
        threading.Thread(daemon=True, target=self.thread_ast_all_logic, args=(contest, folder_path)).start()

    def thread_ast_all_logic(self, contest, root_folder):
        """
        ฟังก์ชันหลักที่ทำงานบนเธรดเบื้องหลัง (Background Logic) สำหรับรัน AST Analysis เหมาหมดทุกข้อ
        """
        c_id = contest['id']
        
        # 1. ทำความสะอาดชื่อการแข่งขัน เพื่อไม่ให้มีอักขระแปลกประหลาดที่จะทำให้สร้างชื่อโฟลเดอร์ไม่ได้ (Sanitization)
        safe_c_name = "".join([c for c in contest['name'] if c.isalnum() or c in (' ', '_')]).strip()
        
        # สร้างโฟลเดอร์ย่อยเฉพาะของการแข่งขันนี้ ไว้ในโฟลเดอร์หลักที่ผู้ใช้เลือก
        export_folder = os.path.join(root_folder, f"AST_Report_{c_id}_{safe_c_name}")
        if not os.path.exists(export_folder): os.makedirs(export_folder)
            
        problems = contest['problems_data']
        total_probs = len(problems)
        success_count = 0
        
        # 2. วนลูปรันโหมด Matrix ให้กับโจทย์ทีละข้อ
        for idx, p in enumerate(problems):
            # ส่งคำสั่งไปอัปเดตข้อความบนปุ่มกดที่เธรดหลัก เพื่อแจ้งสถานะ (เช่น Processing 1/5)
            self.ui(self.btn_ast_all.config, text=f"Processing {idx+1}/{total_probs}")
            
            # เรียกใช้ฟังก์ชันแกนหลักในการดึงและแปลงโค้ด AST (กระบวนการนี้ใช้เวลาและทรัพยากรสูง)
            records = self.prepare_records_for_problem(c_id, p['id'])
            
            # หากโจทย์ข้อนี้ไม่มีใครส่งเลย หรือมีคนส่งแค่คนเดียว ให้ข้ามไปข้อถัดไป
            if not records or len(records) < 2: continue
                
            # เตรียมโครงสร้างตาราง Matrix ว่างๆ ไว้รอรับคะแนน
            teams_list = [r['team_name'] for r in records]
            matrix = {t: {t2: 0.0 for t2 in teams_list} for t in teams_list}
            
            # วนลูปเปรียบเทียบทุกทีมเข้าด้วยกัน (All vs All)
            for A in records:
                for B in records:
                    if A['team_id'] == B['team_id']:
                        matrix[A['team_name']][B['team_name']] = 100.0
                        continue
                        
                    # คำนวณความเหมือนด้วยอัลกอริทึม ZSS (Tree Edit Distance)
                    dist = simple_distance(A['tree'], B['tree'])
                    max_nodes = max(A['node_count'], B['node_count'])
                    sim = max(0.0, 1.0 - (dist / max_nodes)) if max_nodes > 0 else 1.0
                    matrix[A['team_name']][B['team_name']] = sim * 100
                    
            # 3. นำคะแนนที่ได้ มาสร้างไฟล์ CSV แบบเงียบๆ (ไม่ต้องแสดงหน้าต่าง Save Dialog)
            # ทำความสะอาดชื่อโจทย์เพื่อความปลอดภัยในการเซฟไฟล์
            safe_p_name = "".join([c for c in p['name'] if c.isalnum() or c in (' ', '_')]).strip()
            csv_path = os.path.join(export_folder, f"matrix_{p['id']}_{safe_p_name}.csv")
            
            try:
                # เขียนไฟล์ CSV แบบรองรับภาษาไทย
                with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Team'] + teams_list)
                    for t1 in teams_list:
                        row = [t1]
                        for t2 in teams_list: row.append(f'{matrix[t1][t2]:.2f}')
                        writer.writerow(row)
                success_count += 1
            except: pass # หากเซฟไฟล์ไม่ได้ ให้ข้ามไปข้อถัดไปเงียบๆ
            
        # 4. เมื่อรันครบทุกข้อแล้ว คืนค่าปุ่มให้กลับมาเป็นข้อความปกติ และปลดล็อกให้ใช้งานได้
        self.ui(self.btn_ast_all.config, state='normal', text='AST All Problems (CSV)')
        # แสดงหน้าต่างแจ้งสรุปผลการทำงาน
        self.ui(messagebox.showinfo, 'Success', f'Generated {success_count} reports in:\n{export_folder}')

    def init_ast_result_frame(self):
        """
        ฟังก์ชันสำหรับสร้างโครงสร้างหน้าต่าง 'รายงานผลความคล้ายคลึง' (Similarity Report)
        เพื่อแสดงผลตารางจับคู่ทีมที่มีโอกาสคัดลอกโค้ดกัน
        """
        tk.Label(self.frame_ast_result, text='Similarity Report', font=self.font_header).pack(pady=10)
        
        # ป้ายสำหรับระบุชื่อโจทย์ที่กำลังตรวจสอบอยู่ (จะถูกอัปเดตข้อความในภายหลัง)
        self.lbl_res_prob = tk.Label(self.frame_ast_result, text='Problem', font=('Segoe UI', 12), fg='#1976D2')
        self.lbl_res_prob.pack(pady=5)
        
        # สร้างคอนเทนเนอร์สำหรับวางตาราง
        table_frame = tk.Frame(self.frame_ast_result)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # --- เริ่มส่วนการสร้างตาราง (Treeview) ---
        columns = ('Rank', 'Team A', 'Team B', 'Similarity')
        # สร้างวิดเจ็ต Treeview ซึ่งทำหน้าที่เป็นตารางแสดงผล (Data Grid)
        self.tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)
        
        # กำหนดหัวคอลัมน์และความกว้างของแต่ละคอลัมน์
        self.tree.heading('Rank', text='Rank')
        self.tree.column('Rank', width=60, anchor='center')
        self.tree.heading('Team A', text='Student A')
        self.tree.column('Team A', width=150)
        self.tree.heading('Team B', text='Student B')
        self.tree.column('Team B', width=150)
        self.tree.heading('Similarity', text='Match')
        self.tree.column('Similarity', width=100, anchor='center') # แสดงเปอร์เซ็นต์ไว้ตรงกลาง
        
        # สร้างแถบเลื่อน (Scrollbar) แนวตั้ง และผูกเข้ากับตาราง Treeview
        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.tree.pack(side='left', fill='both', expand=True)
        # --- จบส่วนการสร้างตาราง ---
        
        # ผูกเหตุการณ์: เมื่อดับเบิลคลิกเมาส์ซ้าย (<Double-1>) ที่แถวใดในตาราง ให้เรียกฟังก์ชันโชว์รายละเอียด (เหตุผลที่โค้ดเหมือนกัน)
        self.tree.bind('<Double-1>', self.on_tree_double_click)
        
        # ปุ่มย้อนกลับไปยังหน้าเลือกโหมดวิเคราะห์ (Mode Select)
        btn_frame = tk.Frame(self.frame_ast_result)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text='Back to Mode Select', command=lambda: self.show_frame(self.frame_mode_select)).pack(side='left', padx=10)

    def render_ast_results(self, results, problem_name):
        """
        ฟังก์ชันสำหรับ 'วาด' ข้อมูลผลลัพธ์การคำนวณ AST ลงไปในตาราง (Treeview)
        """
        # บันทึกข้อมูลผลลัพธ์เก็บไว้ในตัวแปรคลาส เพื่อใช้อ้างอิงเวลาผู้ใช้ดับเบิลคลิกดูเหตุผล
        self.latest_ast_results = results
        # อัปเดตชื่อโจทย์บนหน้าจอ
        self.lbl_res_prob.config(text=f'Problem: {problem_name}')
        
        # ล้างข้อมูลเก่าที่อาจค้างอยู่ในตารางออกให้หมดก่อน
        for item in self.tree.get_children(): self.tree.delete(item)
            
        # วนลูปอ่านข้อมูลผลลัพธ์ (ที่ถูกเรียงลำดับจากเหมือนมากไปน้อยมาแล้ว)
        for idx, res in enumerate(results):
            # ตรวจสอบเปอร์เซ็นต์ความเหมือน (sim_pct) เพื่อกำหนดแท็กสี (Tag) ให้กับแถวนั้นๆ
            # เกิน 80% = เสี่ยงสูง (high), เกิน 60% = เสี่ยงปานกลาง (med), ที่เหลือ = ปกติ (normal)
            tag = 'high' if res['sim_pct'] >= 80 else 'med' if res['sim_pct'] >= 60 else 'normal'
            
            # จัดเตรียมข้อมูลที่จะใส่ลงในแต่ละคอลัมน์
            row = (idx+1, res['teamA'], res['teamB'], f'{res["sim_pct"]:.2f}%')
            # แทรกลงในตาราง โดยแนบ tag สีเข้าไปด้วย
            self.tree.insert('', 'end', values=row, tags=(tag,))
            
        # ตั้งค่าสีของตัวอักษรตาม Tag ที่เรากำหนดไว้
        self.tree.tag_configure('high', foreground='red')      # เสี่ยงสูงให้ตัวอักษรสีแดง
        self.tree.tag_configure('med', foreground='#FF9800')   # เสี่ยงปานกลางให้ตัวอักษรสีส้ม
        
        # สลับหน้าจอมาที่หน้ารายงานผล
        self.show_frame(self.frame_ast_result)

    def on_tree_double_click(self, event):
        """
        ฟังก์ชันจัดการเหตุการณ์เมื่อผู้ใช้ 'ดับเบิลคลิก' ที่แถวในตาราง
        เพื่อเปิดหน้าต่างป๊อปอัปแจ้ง 'เหตุผล' ว่าทำไมระบบถึงให้คะแนนความเหมือนคู่โค้ดนี้สูง
        """
        # ตรวจสอบว่าผู้ใช้คลิกที่ไอเทม (แถว) ไหนในตาราง
        item = self.tree.selection()[0]
        # หาว่าไอเทมนั้นอยู่ลำดับที่เท่าไหร่ (Index)
        idx = self.tree.index(item)
        
        # ดึงข้อมูลผลลัพธ์แบบเต็มๆ จากตัวแปรอ้างอิงที่เก็บไว้ตอนเรนเดอร์ตาราง
        res = self.latest_ast_results[idx]
        
        # ดึงคำอธิบาย (Reason) มาจัดรูปแบบใหม่ โดยเปลี่ยนช่องว่างพิเศษให้เป็นการขึ้นบรรทัดใหม่ (\n\n) ให้อ่านง่าย
        formatted_reason = res['reason'].replace('  ', '\n\n')
        # แสดงหน้าต่างแจ้งเตือน (Pop-up) พร้อมเหตุผลเชิงลึกประกอบการพิจารณา
        messagebox.showinfo('Detail', f'Similarity Justification:\n\n{formatted_reason}')

    def download_all_from_detail(self):
        """
        ฟังก์ชันสำหรับปุ่มทางลัด (Shortcut) สั่งดาวน์โหลดโค้ด 'ทุกข้อ' ของการแข่งขันนี้
        จากหน้าแสดงรายละเอียดการแข่งขัน (Detail Frame) ได้โดยตรง
        """
        c_id = self.selected_contest_id
        # ค้นหาข้อมูลการแข่งขันปัจจุบันจากแคช
        contest = next((c for c in CACHE_DATA['contests'] if str(c['id']) == str(c_id)), None)
        if not contest: return
        
        # เปิดหน้าต่างให้ผู้ใช้เลือกโฟลเดอร์หลักที่จะเก็บไฟล์
        folder_path = filedialog.askdirectory(title='Select Destination Folder')
        if not folder_path: return # ถ้ากดยกเลิกให้หยุดทำงาน
        
        # ดึงรหัสโจทย์ทั้งหมด (ทุกข้อ) ของการแข่งขันนี้ออกมายัดใส่ลิสต์
        selected_problem_ids = [p['id'] for p in contest['problems_data']]
        
        # ล็อกปุ่มกดเพื่อป้องกันการสั่งดาวน์โหลดซ้ำ
        self.btn_dl_all_detail.config(state='disabled')
        
        # เรียกใช้งานเธรดเบื้องหลังเพื่อไปดาวน์โหลดโค้ดทั้งหมด (เหมือนกระบวนการ Bulk Download)
        threading.Thread(daemon=True, target=self.thread_download_all_from_detail, args=(contest, selected_problem_ids, folder_path)).start()   
    def download_all_for_this_problem(self):
        """
        ฟังก์ชันสำหรับปุ่มดาวน์โหลดไฟล์ซอร์สโค้ด 'ทุกการส่งงาน' ที่อยู่ในโจทย์ข้อปัจจุบัน
        (ถูกเรียกใช้จากหน้า Stat Frame)
        """
        # 1. ตรวจสอบความพร้อมของรหัสการแข่งขันและข้อมูลโจทย์
        c_id = self.selected_contest_id
        if not c_id or not self.current_problem_data: return
        
        # 2. เปิดหน้าต่างให้ผู้ใช้เลือกโฟลเดอร์ปลายทาง
        folder_path = filedialog.askdirectory(title='Select Destination Folder')
        if not folder_path: return # หากกดยกเลิกให้หยุดการทำงาน
        
        # 3. ล็อกปุ่มกดเพื่อป้องกันการกดซ้ำซ้อน
        self.btn_dl_prob_stat.config(state='disabled')
        
        # 4. สร้างเธรดแยกเพื่อไปประมวลผลการดาวน์โหลดเบื้องหลัง (ป้องกันหน้าต่าง Tkinter ค้าง)
        # (หมายเหตุ: ฟังก์ชัน thread_download_problem_stat จะเป็นตัวรับช่วงต่อในการจัดการไฟล์)
        threading.Thread(daemon=True, target=self.thread_download_problem_stat, args=(c_id, self.current_problem_data['id'], folder_path)).start()
        
    def download_all_team_history(self):
        """
        ฟังก์ชันสำหรับปุ่มดาวน์โหลดไฟล์ซอร์สโค้ด 'ทุกเวอร์ชัน' ในประวัติการส่งงานของทีมใดทีมหนึ่ง
        (ถูกเรียกใช้จากหน้า History Frame)
        """
        # 1. ตรวจสอบว่ามีข้อมูลของนักศึกษาและมีประวัติการส่งงาน (History) จริงหรือไม่
        if not self.current_student_data or not self.current_student_data.get('history'): return
        
        # 2. เปิดหน้าต่างให้ผู้ใช้เลือกโฟลเดอร์ปลายทาง
        folder_path = filedialog.askdirectory(title='Select Destination Folder')
        if not folder_path: return
        
        # 3. ล็อกปุ่มกดเพื่อป้องกันการสั่งงานซ้ำ
        self.btn_dl_team_hist.config(state='disabled')
        
        # 4. เรียกใช้งานเธรดเบื้องหลังเพื่อเริ่มกระบวนการดาวน์โหลดประวัติทั้งหมด
        threading.Thread(daemon=True, target=self.thread_download_team_history, args=(self.current_student_data, folder_path)).start()

    def thread_download_team_history(self, student_data, root_dir):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง ทำหน้าที่ดาวน์โหลดซอร์สโค้ดตามประวัติการส่งงานของทีม
        และจัดเก็บลงในโฟลเดอร์เฉพาะอย่างเป็นระเบียบ
        """
        c_id = self.selected_contest_id
        team_id = student_data['id']
        history = student_data['history'] # ดึงลิสต์ประวัติการส่งงานทั้งหมดของทีมนี้มา
        
        # สร้างเส้นทางโฟลเดอร์ย่อยเฉพาะสำหรับทีมนี้ (เช่น Root/Team_123_History)
        team_folder = os.path.join(root_dir, f"Team_{team_id}_History")
        # หากโฟลเดอร์ยังไม่มีอยู่จริง ให้สร้างขึ้นมาใหม่
        if not os.path.exists(team_folder): os.makedirs(team_folder)

        success_count = 0 # ตัวนับจำนวนไฟล์ที่ดาวน์โหลดและบันทึกสำเร็จ
        
        # วนลูปอ่านประวัติการส่งงานทีละครั้ง
        for i, sub in enumerate(history):
            # ส่งคำสั่งให้เธรดหลักอัปเดตป้ายสถานะความคืบหน้า (เช่น Downloading 1 / 5)
            self.ui(self.lbl_hist_dl_status.config, text=f'Downloading {i+1} / {len(history)}')
            
            # เรียก API เพื่อดึงข้อมูลไฟล์ซอร์สโค้ดของการส่งงานครั้งนี้
            src = fetch_data(f'/api/v4/contests/{c_id}/submissions/{sub["id"]}/source-code')
            if src:
                try:
                    # เปิดไฟล์ในโหมด 'wb' (Write Binary) โดยตั้งชื่อไฟล์เป็น รหัสการส่ง_ชื่อไฟล์เดิม
                    with open(os.path.join(team_folder, f'{sub["id"]}_{src[0]["filename"]}'), 'wb') as f:
                        # ถอดรหัส (Decode) ข้อมูล Base64 กลับเป็นโค้ดปกติ และเขียนลงไฟล์
                        f.write(base64.b64decode(src[0]['source']))
                    success_count += 1
                except: pass # หากเกิดปัญหาในการเขียนไฟล์ (เช่น ชื่อไฟล์มีอักขระพิเศษ) ให้ข้ามไป
                
            # หน่วงเวลา 0.1 วินาที ลดภาระการส่ง Request ถี่เกินไปจนอาจถูกเซิร์ฟเวอร์ปฏิเสธการเชื่อมต่อ
            time.sleep(0.1)

        # เมื่อดาวน์โหลดครบทุกไฟล์แล้ว ส่งคำสั่งอัปเดตสถานะให้เป็น Done
        self.ui(self.lbl_hist_dl_status.config, text=f'Done! Downloaded {success_count}/{len(history)} files.')
        # แสดงหน้าต่างแจ้งเตือนสรุปผลการทำงาน พร้อมระบุที่อยู่ของโฟลเดอร์
        self.ui(messagebox.showinfo, 'Success', f'Downloaded {success_count} files into:\n{team_folder}')
        # ปลดล็อกปุ่มกดให้กลับมาใช้งานได้ตามปกติ
        self.ui(self.btn_dl_team_hist.config, state='normal')   
     
    def thread_download_problem_stat(self, c_id, p_id, root_dir):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง ทำหน้าที่ดาวน์โหลดซอร์สโค้ดของ 'ทุกทีม' 
        เฉพาะใน 'โจทย์ข้อที่เลือก' (Problem) และจัดเก็บลงโฟลเดอร์อย่างเป็นระบบ
        """
        # 1. ตรวจสอบและสร้างโฟลเดอร์หลัก หากยังไม่มีอยู่จริง
        if not os.path.exists(root_dir): os.makedirs(root_dir)
        
        # 2. อัปเดตสถานะบนหน้าจอเพื่อให้ผู้ใช้ทราบว่าระบบกำลังเริ่มทำงาน
        self.ui(self.lbl_stat_dl_status.config, text='Fetching submission list...')
        
        # 3. ดึงข้อมูลประวัติการส่งงานทั้งหมดของการแข่งขันนี้มาก่อน
        subs = fetch_data(f'/api/v4/contests/{c_id}/submissions')
        if not subs:
            # หากไม่มีใครเคยส่งงานเลย ให้แจ้งสถานะและปลดล็อกปุ่มกด
            self.ui(self.lbl_stat_dl_status.config, text='No submissions found')
            self.ui(self.btn_dl_prob_stat.config, state='normal')
            return
            
        # 4. คัดกรองเฉพาะการส่งงานที่ตรงกับรหัสโจทย์ (p_id) ที่เรากำลังสนใจ
        subs_to_dl = [s for s in subs if str(s['problem_id']) == str(p_id)]
        success_count = 0
        
        # 5. วนลูปดาวน์โหลดไฟล์ซอร์สโค้ดทีละรายการ
        for i, s in enumerate(subs_to_dl):
            self.ui(self.lbl_stat_dl_status.config, text=f'Downloading {i+1} / {len(subs_to_dl)}')
            
            # เรียก API เพื่อดึงเนื้อหาซอร์สโค้ด
            src = fetch_data(f'/api/v4/contests/{c_id}/submissions/{s["id"]}/source-code')
            if src:
                # สร้างเส้นทางโฟลเดอร์ย่อย: โฟลเดอร์หลัก / รหัสการแข่งขัน / รหัสโจทย์ / รหัสทีม
                path = os.path.join(root_dir, str(c_id), str(p_id), str(s['team_id']))
                if not os.path.exists(path): os.makedirs(path)
                
                try:
                    # เปิดไฟล์เพื่อเขียนข้อมูลไบนารี (ตั้งชื่อไฟล์โดยเอารหัสการส่งนำหน้า เพื่อป้องกันชื่อซ้ำ)
                    with open(os.path.join(path, f'{s["id"]}_{src[0]["filename"]}'), 'wb') as f:
                        # ถอดรหัส Base64 ให้กลับเป็นไฟล์โค้ดปกติแล้วบันทึกลงเครื่อง
                        f.write(base64.b64decode(src[0]['source']))
                    success_count += 1
                except: pass # หากมีปัญหาในการเขียนไฟล์ให้ข้ามไปทำรายการถัดไป
                
            # หน่วงเวลาเล็กน้อยป้องกันการรบกวนเซิร์ฟเวอร์หนักเกินไป
            time.sleep(0.1)
            
        # 6. ดาวน์โหลดเสร็จสิ้น อัปเดตสถานะ โชว์ป๊อปอัปแจ้งเตือน และปลดล็อกปุ่มกด
        self.ui(self.lbl_stat_dl_status.config, text=f'Done! {success_count}/{len(subs_to_dl)} files.')
        self.ui(messagebox.showinfo, 'Success', f'Downloaded {success_count} files')
        self.ui(self.btn_dl_prob_stat.config, state='normal')

    def thread_download_all_from_detail(self, contest, selected_problem_ids, root_dir):
        """
        ฟังก์ชันทำงานบนเธรดเบื้องหลัง ทำหน้าที่ดาวน์โหลดซอร์สโค้ด 'ทุกข้อ' ในการแข่งขัน
        (ถูกเรียกใช้จากปุ่ม Download All Problems ในหน้าแสดงรายละเอียด)
        """
        # 1. ตรวจสอบและสร้างโฟลเดอร์หลัก
        if not os.path.exists(root_dir): os.makedirs(root_dir)
        c_id = contest['id']
        
        # 2. แจ้งสถานะการดึงข้อมูล
        self.ui(self.lbl_detail_status.config, text=f'Fetching submissions for {contest["name"]}...')
        subs = fetch_data(f'/api/v4/contests/{c_id}/submissions')
        if not subs:
            self.ui(self.lbl_detail_status.config, text='No submissions found')
            self.ui(self.btn_dl_all_detail.config, state='normal')
            return
            
        # 3. คัดกรองการส่งงานให้อยู่ในขอบเขตของรหัสโจทย์ที่เลือกมา (เช็กจากลิสต์ selected_problem_ids)
        subs_to_dl = [s for s in subs if str(s['problem_id']) in str(selected_problem_ids)]
        success_count = 0
        
        # 4. วนลูปดาวน์โหลดไฟล์และจัดหมวดหมู่ลงโฟลเดอร์
        for i, s in enumerate(subs_to_dl):
            self.ui(self.lbl_detail_status.config, text=f'Downloading {i+1} / {len(subs_to_dl)}')
            src = fetch_data(f'/api/v4/contests/{c_id}/submissions/{s["id"]}/source-code')
            if src:
                # จัดเรียงโฟลเดอร์ตาม รหัสการแข่งขัน -> รหัสโจทย์ -> รหัสทีม ทำให้โค้ดเป็นระเบียบหาตรวจสอบง่าย
                path = os.path.join(root_dir, str(c_id), str(s['problem_id']), str(s['team_id']))
                if not os.path.exists(path): os.makedirs(path)
                try:
                    with open(os.path.join(path, f'{s["id"]}_{src[0]["filename"]}'), 'wb') as f:
                        f.write(base64.b64decode(src[0]['source']))
                    success_count += 1
                except: pass
            time.sleep(0.1)
            
        # 5. สรุปผลการทำงานและคืนสถานะปุ่ม
        self.ui(self.lbl_detail_status.config, text=f'Done! {success_count}/{len(subs_to_dl)} files.')
        self.ui(messagebox.showinfo, 'Success', f'Downloaded {success_count} files')
        self.ui(self.btn_dl_all_detail.config, state='normal')    

# =====================================================================
# Main Application Entry Point
# (ส่วนจุดเริ่มต้นการทำงานของโปรแกรม)
# =====================================================================

if __name__ == '__main__':
    # 1. สร้างหน้าต่างหลักของ GUI ด้วย Tkinter
    root = tk.Tk()
    
    # 2. นำหน้าต่างหลักไปผูกกับคลาส JudgeApp เพื่อสร้างองค์ประกอบและระบบการทำงานทั้งหมด
    app = JudgeApp(root)
    
    # 3. สั่งให้โปรแกรมเริ่มทำงานและวนลูปรับคำสั่งจากผู้ใช้งาน (Event Loop) อย่างต่อเนื่อง
    root.mainloop()