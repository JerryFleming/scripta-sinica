import os
from ebooklib import epub
from opencc import OpenCC
from bs4 import BeautifulSoup
import opencc  # 添加对opencc库的导入
import time  # 导入time模块以记录处理时间
import hashlib  # 导入hashlib库以生成MD5值
import uuid

def convert_epub_to_vertical_and_traditional(input_epub_path, output_epub_path):
    # 初始化简繁转换器
    cc = OpenCC('s2t')

    # 打开输入的 EPUB 文件
    input_epub = Epub.open(input_epub_path)

    # 创建新的 EPUB 对象
    output_epub = Epub(input_epub.title, creator=input_epub.creator, lang="zh-TW")

    # 遍历输入 EPUB 中的每个章节
    for chapter in input_epub.chapters:
        # 获取章节内容
        content = chapter.content

        # 将内容转换为繁体中文
        traditional_content = cc.convert(content)

        # 创建竖排样式的 HTML 内容
        vertical_content = f"""
        <html>
        <head>
            <style>
                body {{
                    writing-mode: vertical-rl;
                    text-orientation: upright;
                    font-family: serif;
                    line-height: 1.6;
                }}
                .calibre {{
                    -epub-ruby-position: over;
                    -webkit-ruby-position: over;
                    -webkit-text-emphasis-position: over;
                    -webkit-writing-mode: vertical-rl;
                    display: block;
                    font-family: serif, sans-serif;
                    font-size: 1em;
                    text-align: justify;
                    text-justify: inter-ideograph;
                    margin: 0 5pt;
                    padding: 0
                    }}
                .calibre1 {{
                    display: block;
                    line-height: 1.75em;
                    margin: 0
                    }}
            </style>
        </head>
        <body>
            {traditional_content}
        </body>
        </html>
        """

        # 创建新的章节并添加到输出 EPUB 中
        new_chapter = Chapter(chapter.title, content=vertical_content)
        output_epub.add_chapter(new_chapter)

    # 生成输出的 EPUB 文件
    output_epub.create_epub(output_epub_path)
    print(f"转换后的 EPUB 文件已保存到: {output_epub_path}")


def convert_txt_to_vertical_and_traditional(txt_path, epub_path):
    book = epub.EpubBook()
    
    # 获取文件名（不带后缀）
    file_name = os.path.splitext(os.path.basename(txt_path))[0]
    
    # 生成基于文件路径的MD5值
    unique_id = str(uuid.uuid4())
    
    # 设置基本信息
    book.set_identifier(unique_id)  # 使用文件名作为identifier
    book.set_title(file_name)
    book.set_language('zh-tw')
    
    # 添加默认的作者信息
    book.add_author('公版')
    
    # 读取txt文件内容
    with open(txt_path, 'r', encoding='utf-8') as file:
        txt_content = file.read()
    
    # 检查内容是否为空
    if not txt_content.strip():
        txt_content = "本文档内容为空。"
    
    # 将文本内容转换为竖排繁体HTML
    vertical_traditional_html = convert_to_vertical_traditional_html(txt_content)
    
    # 创建一个EpubHtml对象
    c1 = epub.EpubHtml(title='第一章', file_name='chap_01.xhtml', lang='zh-tw')
    c1.content = vertical_traditional_html
    
    # 确保内容是字符串
    assert isinstance(c1.content, str), "Content must be a string"
    
    # 将章节添加到书中
    book.add_item(c1)
    
    # 定义Table Of Contents
    book.toc = (epub.Link('chap_01.xhtml', 'Chapter 1', 'chap_01'),)
    
    # 添加默认NCX和导航文件
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    
    # 定义CSS样式
    style = 'BODY {color: white;}'
    nav_css = epub.EpubItem(uid="style_nav", file_name="style/nav.css", media_type="text/css", content=style)
    
    # 添加CSS文件
    book.add_item(nav_css)
    
    # 定义SPINE
    book.spine = ['nav', c1]
    
    # 添加 page-progression-direction 属性
    book.set_direction("rtl")
    
    # 写入EPUB文件
    epub.write_epub(epub_path, book, {})


def convert_to_vertical_traditional_html(txt_content):
    # 将简体中文转换为繁体中文
    txt_content = convert_to_traditional(txt_content)
    
    soup = BeautifulSoup('<html><head><title>Document</title></head><body></body></html>', 'html.parser')
    head = soup.head
    
    # 添加meta标签以指定文本方向为从右到左
    meta_tag = soup.new_tag('meta', attrs={'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0'})
    head.append(meta_tag)
    meta_tag = soup.new_tag('meta', attrs={'name': 'primary-writing-mode', 'content': 'vertical-ltr'})
    head.append(meta_tag)
    
    # 添加CSS样式以指定文本方向为从右到左
    style_tag = soup.new_tag('style')
    style_tag.string = 'body { direction: rtl; }'
    head.append(style_tag)
    
    body = soup.body
    
    # 创建一个<div>标签并添加文本内容
    div = soup.new_tag('div', style="text-orientation: upright; writing-mode: vertical-rl; display: block;line-height: 1.75em;margin: 0")
    div.string = txt_content
    body.append(div)
    
    return str(soup)


def convert_to_traditional(text):
    cc = opencc.OpenCC('s2t')  # 使用s2t.json配置文件进行简繁转换
    return cc.convert(text)

def convert_all_txt_to_epub(root_folder):
    
    # 递归遍历文件夹
    i=0
    for foldername, subfolders, filenames in os.walk(root_folder):
        for filename in filenames:
            if filename.endswith('.txt') and not filename.startswith('._'):
                i+=1
                input_txt_path = os.path.join(foldername, filename)
                output_epub_path = os.path.join(foldername, os.path.splitext(filename)[0] + '.epub')
                
                # 记录开始处理时间
                start_time = time.time()
                
                # 打印正在处理的文件路径和名称
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} 正在处理文件 {i} : {input_txt_path}")
                
                # 检查output_epub_path是否存在，如果存在则删除
                if os.path.exists(output_epub_path):
                    os.remove(output_epub_path)  # 删除已存在的输出EPUB文件
                
                convert_txt_to_vertical_and_traditional(input_txt_path, output_epub_path)  # 调用转换函数进行转换
                
                # 记录结束处理时间
                end_time = time.time()
                
                # 计算处理时间
                processing_time = end_time - start_time
                
                # 打印处理时间
                print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} 文件 {input_txt_path} 处理完成，耗时: {processing_time:.2f} 秒")

                # input("按回车键继续处理下一个文件...")

if __name__ == "__main__":
    root_folder = '/Volumes/250G/scripta-sinica'  # 替换为你的根文件夹路径
    convert_all_txt_to_epub(root_folder)  # 调用递归转换函数进行转换
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())} 所有文件处理完成。")