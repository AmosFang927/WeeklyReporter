#!/usr/bin/env python3
"""
邮件发送模块
负责发送转换报告邮件
"""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from utils.logger import print_step
import config
import pandas as pd

class EmailSender:
    """邮件发送器"""
    
    def __init__(self):
        self.sender = config.EMAIL_SENDER
        self.default_receivers = config.EMAIL_RECEIVERS
        self.pub_email_mapping = config.PUB_EMAIL_MAPPING
        self.pub_email_enabled = getattr(config, 'PUB_EMAIL_ENABLED', {})  # Pub邮件开关
        self.auto_cc_email = getattr(config, 'EMAIL_AUTO_CC', None)  # 自动抄送邮箱
        self.password = config.EMAIL_PASSWORD
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.enable_tls = config.EMAIL_ENABLE_TLS
        self.include_attachments = config.EMAIL_INCLUDE_ATTACHMENTS
        self.include_feishu_links = config.EMAIL_INCLUDE_FEISHU_LINKS
        self.subject_template = config.EMAIL_SUBJECT_TEMPLATE
    
    def send_pub_reports(self, pub_summary, feishu_upload_result=None, report_date=None):
        """
        按Pub分别发送转换报告邮件
        
        Args:
            pub_summary: Pub汇总数据字典，格式：
                {
                    'pub_name': {
                        'records': 数量,
                        'amount_formatted': '$金额',
                        'file_path': '文件路径'
                    }
                }
            feishu_upload_result: 飞书上传结果
            report_date: 报告日期（用于邮件标题和内容）
        
        Returns:
            dict: 发送结果汇总
        """
        print_step("Pub邮件发送", "开始按Pub分别发送转换报告邮件")
        
        # 检查配置
        if self.password == "your_gmail_app_password_here":
            error_msg = "邮件密码未配置，请在config.py中设置EMAIL_PASSWORD"
            print_step("配置错误", f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        
        results = {
            'success': True,
            'total_sent': 0,
            'total_failed': 0,
            'pub_results': {}
        }
        
        for pub_name, pub_data in pub_summary.items():
            try:
                # 检查该Pub是否启用邮件发送
                if not self.pub_email_enabled.get(pub_name, False):
                    print_step(f"Pub邮件-{pub_name}", f"⚠️ 邮件发送已关闭，跳过")
                    results['pub_results'][pub_name] = {'success': True, 'skipped': True, 'reason': '邮件发送已关闭'}
                    continue
                
                # 获取该Pub的收件人
                receivers = self.pub_email_mapping.get(pub_name, self.default_receivers)
                
                # 准备该Pub的邮件数据
                email_data = self._prepare_pub_email_data(pub_name, pub_data, report_date)
                
                # 获取该Pub的飞书文件信息
                pub_feishu_info = self._get_pub_feishu_info(pub_name, feishu_upload_result)
                
                # 发送邮件
                result = self._send_single_pub_email(
                    pub_name, 
                    email_data, 
                    [pub_data['file_path']], 
                    receivers,
                    pub_feishu_info,
                    report_date
                )
                
                results['pub_results'][pub_name] = result
                if result['success'] and not result.get('skipped'):
                    results['total_sent'] += 1
                elif result.get('skipped'):
                    # 跳过的不计入失败，但也不计入成功发送
                    pass
                else:
                    results['total_failed'] += 1
                    results['success'] = False
                    
            except Exception as e:
                error_msg = f"Pub {pub_name} 邮件发送失败: {str(e)}"
                print_step("Pub邮件失败", f"❌ {error_msg}")
                results['pub_results'][pub_name] = {'success': False, 'error': error_msg}
                results['total_failed'] += 1
                results['success'] = False
        
        if results['success']:
            print_step("Pub邮件完成", f"✅ 成功发送 {results['total_sent']} 个Pub报告邮件")
        else:
            print_step("Pub邮件部分失败", f"⚠️ 发送完成：成功 {results['total_sent']} 个，失败 {results['total_failed']} 个")
        
        return results
    
    def send_report_email(self, report_data, file_paths=None, feishu_upload_result=None):
        """
        发送转换报告邮件（兼容性保留，建议使用send_pub_reports）
        
        Args:
            report_data: 报告数据字典
            file_paths: Excel文件路径列表
            feishu_upload_result: 飞书上传结果
        
        Returns:
            dict: 发送结果
        """
        print_step("邮件发送", "开始发送转换报告邮件")
        
        # 检查配置
        if self.password == "your_gmail_app_password_here":
            error_msg = "邮件密码未配置，请在config.py中设置EMAIL_PASSWORD"
            print_step("配置错误", f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
        
        try:
            # 创建邮件对象
            msg = self._create_email_message(report_data, file_paths, feishu_upload_result, self.default_receivers)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.enable_tls:
                    server.starttls()
                
                server.login(self.sender, self.password)
                text = msg.as_string()
                server.sendmail(self.sender, self.default_receivers, text)
            
            print_step("邮件发送成功", f"✅ 邮件已发送给 {', '.join(self.default_receivers)}")
            return {
                'success': True,
                'recipients': self.default_receivers,
                'attachments_count': len(file_paths) if file_paths and self.include_attachments else 0
            }
            
        except Exception as e:
            error_msg = f"邮件发送失败: {str(e)}"
            print_step("邮件发送失败", f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _send_single_pub_email(self, pub_name, email_data, file_paths, receivers, feishu_info, report_date=None):
        """发送单个Pub的邮件"""
        try:
            # 添加抄送邮箱（从配置读取）
            cc_email = self.auto_cc_email
            all_recipients = receivers.copy()
            if cc_email and cc_email not in receivers:
                all_recipients.append(cc_email)
            
            # 创建邮件对象
            msg = self._create_pub_email_message(pub_name, email_data, file_paths, receivers, feishu_info, report_date, cc_email)
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.enable_tls:
                    server.starttls()
                
                server.login(self.sender, self.password)
                text = msg.as_string()
                server.sendmail(self.sender, all_recipients, text)
            
            cc_info = f" (抄送: {cc_email})" if cc_email else ""
            print_step(f"Pub邮件-{pub_name}", f"✅ 邮件已发送给 {', '.join(receivers)}{cc_info}")
            return {
                'success': True,
                'recipients': receivers,
                'cc_recipients': [cc_email] if cc_email else [],
                'attachments_count': len(file_paths) if file_paths and self.include_attachments else 0
            }
            
        except Exception as e:
            error_msg = f"发送失败: {str(e)}"
            print_step(f"Pub邮件-{pub_name}", f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _prepare_pub_email_data(self, pub_name, pub_data, report_date=None):
        """准备Pub邮件数据"""
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")
        
        # 从Excel文件中计算真实的销售总额
        real_total_amount = self._calculate_sales_amount_from_excel(pub_data.get('file_path'))
        
        return {
            'pub_name': pub_name,
            'total_records': pub_data.get('records', 0),
            'total_amount': real_total_amount,
            'start_date': report_date,
            'end_date': report_date,
            'report_date': report_date,
            'main_file': os.path.basename(pub_data.get('file_path', ''))
        }
    
    def _calculate_sales_amount_from_excel(self, file_path):
        """从Excel文件中计算Sales Amount总额"""
        try:
            if not file_path or not os.path.exists(file_path):
                print_step("金额计算", f"⚠️ 文件不存在: {file_path}")
                return '$0.00'
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            print_step("金额计算", f"📊 正在计算 {os.path.basename(file_path)} 的销售总额...")
            
            # 查找sale_amount列
            if 'sale_amount' in df.columns:
                # 计算总额
                total = df['sale_amount'].sum()
                formatted_amount = f"${total:.2f}"
                print_step("金额计算", f"💰 {os.path.basename(file_path)} 销售总额: {formatted_amount}")
                return formatted_amount
            else:
                print_step("金额计算", f"⚠️ 未找到sale_amount列在文件 {os.path.basename(file_path)}")
                return '$0.00'
                
        except Exception as e:
            print_step("金额计算", f"❌ 计算金额失败 {os.path.basename(file_path)}: {str(e)}")
            return '$0.00'
    
    def _get_pub_feishu_info(self, pub_name, feishu_upload_result):
        """获取该Pub的飞书文件信息"""
        if not feishu_upload_result or not feishu_upload_result.get('uploaded_files'):
            return None
        
        # 查找该Pub对应的飞书文件
        for file_info in feishu_upload_result['uploaded_files']:
            filename = file_info.get('filename', '')
            if filename.startswith(pub_name):
                return {
                    'success': True,
                    'uploaded_files': [file_info]
                }
        
        return None
    
    def _create_pub_email_message(self, pub_name, email_data, file_paths, receivers, feishu_info, report_date=None, cc_email=None):
        """创建Pub邮件消息"""
        # 生成邮件主题 - 使用报告日期
        if report_date is None:
            report_date = datetime.now().strftime("%Y-%m-%d")
        subject = self.subject_template.format(date=report_date)
        
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = ", ".join(receivers)
        if cc_email:
            msg['Cc'] = cc_email
        msg['Subject'] = subject
        
        # 生成邮件正文
        body = self._generate_pub_email_body(pub_name, email_data, feishu_info)
        msg.attach(MIMEText(body, 'html'))
        
        # 添加附件
        if file_paths and self.include_attachments:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    self._attach_file(msg, file_path)
        
        return msg
    
    def _create_email_message(self, report_data, file_paths=None, feishu_upload_result=None, receivers=None):
        """创建邮件消息（兼容性保留）"""
        if receivers is None:
            receivers = self.default_receivers
            
        # 生成邮件主题
        today = datetime.now().strftime("%Y-%m-%d")
        subject = self.subject_template.format(date=today)
        
        # 创建邮件对象
        msg = MIMEMultipart()
        msg['From'] = self.sender
        msg['To'] = ", ".join(receivers)
        msg['Subject'] = subject
        
        # 生成邮件正文
        body = self._generate_email_body(report_data, feishu_upload_result)
        msg.attach(MIMEText(body, 'html'))
        
        # 添加附件
        if file_paths and self.include_attachments:
            for file_path in file_paths:
                if os.path.exists(file_path):
                    self._attach_file(msg, file_path)
        
        return msg
    
    def _load_html_template(self, template_name):
        """加载HTML模板文件"""
        try:
            template_path = os.path.join('templates', template_name)
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print_step("模板加载", f"❌ 加载模板失败 {template_name}: {str(e)}")
            return None
    
    def _generate_pub_email_body(self, pub_name, email_data, feishu_info):
        """生成Pub专用邮件正文"""
        report_date = email_data.get('report_date', datetime.now().strftime("%Y-%m-%d"))
        completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 从email_data获取Pub专用数据
        total_records = email_data.get('total_records', 0)
        total_amount = email_data.get('total_amount', '$0.00')
        start_date = email_data.get('start_date', report_date)
        end_date = email_data.get('end_date', report_date)
        main_file = email_data.get('main_file', f'{pub_name}_ConversionReport_{report_date}.xlsx')
        
        # 加载HTML模板
        template = self._load_html_template('email_template.html')
        if not template:
            # 如果模板加载失败，使用备用的简单HTML
            return self._generate_fallback_email_body(pub_name, email_data, feishu_info)
        
        # 准备飞书链接部分
        feishu_section = ""
        if feishu_info and self.include_feishu_links:
            if feishu_info.get('success') and feishu_info.get('uploaded_files'):
                feishu_template = self._load_html_template('feishu_section.html')
                if feishu_template:
                    feishu_links = ""
                    for file_info in feishu_info['uploaded_files']:
                        filename = file_info.get('filename', '')
                        
                        # 优先使用飞书返回的URL
                        feishu_url = file_info.get('url')
                        if not feishu_url:
                            # 如果没有url字段，尝试用file_token构造
                            file_token = file_info.get('file_token') or file_info.get('file_id')
                            if file_token:
                                feishu_url = f"https://bytedance.feishu.cn/sheets/{file_token}"
                        
                        if feishu_url:
                            feishu_links += f'<li><a href="{feishu_url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold;">{filename}</a></li>'
                        else:
                            feishu_links += f'<li>{filename} (已上传)</li>'
                    
                    feishu_section = feishu_template.replace('{{feishu_links}}', feishu_links)
        
        # 替换模板中的占位符
        body = template.replace('{{date}}', report_date)
        body = body.replace('{{partner_name}}', pub_name)  # 注意：这里改为partner_name
        body = body.replace('{{start_date}}', start_date)
        body = body.replace('{{end_date}}', end_date)
        body = body.replace('{{total_records}}', str(total_records))
        body = body.replace('{{total_amount}}', total_amount)
        body = body.replace('{{main_file}}', main_file)
        body = body.replace('{{feishu_section}}', feishu_section)
        body = body.replace('{{completion_time}}', completion_time)
        
        return body
    
    def _generate_fallback_email_body(self, pub_name, email_data, feishu_info):
        """生成备用的简单邮件正文（当模板加载失败时使用）"""
        report_date = email_data.get('report_date', datetime.now().strftime("%Y-%m-%d"))
        completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        total_records = email_data.get('total_records', 0)
        total_amount = email_data.get('total_amount', '$0.00')
        start_date = email_data.get('start_date', report_date)
        end_date = email_data.get('end_date', report_date)
        main_file = email_data.get('main_file', f'{pub_name}_ConversionReport_{report_date}.xlsx')
        
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hi Partners,</p>
            <p>Conversion Report + {report_date} 如附件，请查收。</p>
            
            <h3 style="color: #1f4e79;">📊 {pub_name} 报告摘要:</h3>
            <ul style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff;">
                <li><strong>Partner:</strong> {pub_name}</li>
                <li><strong>日期范围:</strong> {start_date} 至 {end_date}</li>
                <li><strong>总转换数:</strong> {total_records} 条</li>
                <li><strong>Total Sales Amount:</strong> {total_amount}</li>
            </ul>
            
            <h3 style="color: #1f4e79;">📁 附件文件:</h3>
            <ul><li><strong>{main_file}</strong></li></ul>
        """
        
        # 飞书文件链接
        if feishu_info and self.include_feishu_links:
            if feishu_info.get('success') and feishu_info.get('uploaded_files'):
                body += f'<h3 style="color: #1f4e79;">☁️ 飞书文件链接:</h3><ul>'
                for file_info in feishu_info['uploaded_files']:
                    filename = file_info.get('filename', '')
                    
                    # 优先使用飞书返回的URL
                    feishu_url = file_info.get('url')
                    if not feishu_url:
                        # 如果没有url字段，尝试用file_token构造
                        file_token = file_info.get('file_token') or file_info.get('file_id')
                        if file_token:
                            feishu_url = f"https://bytedance.feishu.cn/sheets/{file_token}"
                    
                    if feishu_url:
                        body += f'<li><a href="{feishu_url}" target="_blank" style="color: #007bff; text-decoration: none; font-weight: bold;">{filename}</a></li>'
                    else:
                        body += f'<li>{filename} (已上传)</li>'
                body += "</ul>"
        
        body += f"""
            <p style="margin-top: 30px;"><strong>生成时间:</strong> {completion_time}</p>
            <p style="margin-top: 30px; color: #666;">
                Best regards,<br><strong>AutoReporter Agent</strong>
            </p>
        </body>
        </html>
        """
        
        return body
    
    def _generate_email_body(self, report_data, feishu_upload_result=None):
        """生成邮件正文（兼容性保留）"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # 基本信息
        total_records = report_data.get('total_records', 0)
        total_amount = report_data.get('total_amount', '$0.00')
        start_date = report_data.get('start_date', today)
        end_date = report_data.get('end_date', today)
        completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 构建邮件正文
        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hi Partners,</p>
            
            <p>Conversion Report + {start_date} 如附件，请查收。</p>
            
            <h3 style="color: #1f4e79;">📊 报告摘要:</h3>
            <ul style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff;">
                <li><strong>日期范围:</strong> {start_date} 至 {end_date}</li>
                <li><strong>总转换数:</strong> {total_records} 条</li>
                <li><strong>Total Sales Amount:</strong> {total_amount}</li>
            </ul>
            
            <h3 style="color: #1f4e79;">📁 生成的文件:</h3>
            <ul>
        """
        
        # 添加文件信息
        pub_files = report_data.get('pub_files', [])
        main_file = report_data.get('main_file', f'Pub_WeeklyReport_{today}.xlsx')
        
        body += f"<li><strong>主报告:</strong> {os.path.basename(main_file)}</li>"
        
        for pub_file_info in pub_files:
            if isinstance(pub_file_info, dict):
                filename = pub_file_info.get('filename', '')
                records = pub_file_info.get('records', 0)
                amount = pub_file_info.get('amount', '$0.00')
                body += f"<li><strong>{filename}:</strong> ({records}条, {amount})</li>"
            else:
                # 如果是文件路径字符串
                filename = os.path.basename(pub_file_info)
                body += f"<li><strong>{filename}</strong></li>"
        
        body += "</ul>"
        
        # 飞书上传状态
        if feishu_upload_result:
            if feishu_upload_result.get('success'):
                feishu_status = f"✅ 成功 ({feishu_upload_result.get('success_count', 0)} 个文件)"
                if self.include_feishu_links and feishu_upload_result.get('uploaded_files'):
                    body += f"<h3 style='color: #1f4e79;'>☁️ 飞书文件链接:</h3><ul>"
                    for file_info in feishu_upload_result['uploaded_files']:
                        if file_info.get('url'):
                            body += f"<li><a href='{file_info['url']}'>{file_info['filename']}</a></li>"
                    body += "</ul>"
            else:
                feishu_status = f"❌ 失败 ({feishu_upload_result.get('failed_count', 0)} 个文件)"
        else:
            feishu_status = "未执行"
        
        body += f"""
            <h3 style="color: #1f4e79;">☁️ 飞书上传状态:</h3>
            <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px;">{feishu_status}</p>
            
            <p style="margin-top: 30px;"><strong>生成时间:</strong> {completion_time}</p>
            
            <p style="margin-top: 30px; color: #666;">
                Best regards,<br>
                <strong>AutoReporter Agent</strong>
            </p>
        </body>
        </html>
        """
        
        return body
    
    def _attach_file(self, msg, file_path):
        """添加附件到邮件"""
        try:
            with open(file_path, "rb") as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            msg.attach(part)
            print_step("附件添加", f"已添加附件: {filename}")
            
        except Exception as e:
            print_step("附件错误", f"⚠️ 无法添加附件 {file_path}: {str(e)}")
    
    def test_connection(self):
        """测试邮件服务器连接"""
        print_step("邮件测试", "正在测试邮件服务器连接...")
        
        if self.password == "your_gmail_app_password_here":
            print_step("配置错误", "❌ 邮件密码未配置")
            return False
        
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.enable_tls:
                    server.starttls()
                server.login(self.sender, self.password)
            
            print_step("邮件测试", "✅ 邮件服务器连接成功")
            return True
            
        except Exception as e:
            print_step("邮件测试", f"❌ 邮件服务器连接失败: {str(e)}")
            return False

# 便捷函数
def send_report_email(report_data, file_paths=None, feishu_upload_result=None):
    """
    便捷的邮件发送函数
    
    Args:
        report_data: 报告数据字典
        file_paths: Excel文件路径列表
        feishu_upload_result: 飞书上传结果
    
    Returns:
        dict: 发送结果
    """
    sender = EmailSender()
    return sender.send_report_email(report_data, file_paths, feishu_upload_result)

def test_email_connection():
    """
    测试邮件连接的便捷函数
    
    Returns:
        bool: 连接是否成功
    """
    sender = EmailSender()
    return sender.test_connection() 