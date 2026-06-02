import { escapeHtml } from './ui.js';

export function printPass(visitor) {
    const passWindow = window.open('', '_blank');
    const checkInDate = new Date(visitor.check_in).toLocaleString('ru-RU', { timeZone: 'Europe/Moscow' });
    const safe = {
        full_name: escapeHtml(visitor.full_name),
        company: escapeHtml(visitor.company),
        whom_visit: escapeHtml(visitor.whom_visit),
        purpose: escapeHtml(visitor.purpose),
        id: escapeHtml(visitor.id.toString())
    };
    passWindow.document.write(`<!DOCTYPE html>
<html>
<head>
    <title>Пропуск - ${safe.full_name}</title>
    <style>
        body {
            font-family: 'Times New Roman', serif;
            background: #e0e0e0;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            padding: 20px;
            margin: 0;
        }
        .print-area {
            width: 600px;
            background: white;
            border: 2px solid #0a3e6d;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        }
        .header {
            text-align: center;
            border-bottom: 2px solid #0a3e6d;
            padding-bottom: 15px;
            margin-bottom: 25px;
        }
        .org-name {
            font-size: 24px;
            font-weight: bold;
            color: #0a3e6d;
        }
        .doc-title {
            font-size: 28px;
            font-weight: bold;
            margin: 10px 0;
            text-transform: uppercase;
            color: #1a5d8f;
        }
        .info-row {
            margin-bottom: 15px;
            border-bottom: 1px dotted #ccc;
            padding-bottom: 6px;
        }
        .info-label {
            font-weight: bold;
            display: inline-block;
            width: 160px;
            color: #0a3e6d;
        }
        .info-value {
            display: inline-block;
            font-size: 16px;
        }
        .footer {
            margin-top: 30px;
            border-top: 1px solid #aaa;
            padding-top: 20px;
        }
        .footer-row {
            display: flex;
            justify-content: space-between;
            gap: 30px;
            margin-bottom: 20px;
        }
        .signature-block {
            flex: 1;
            text-align: center;
        }
        .signature-label {
            font-weight: bold;
            margin-bottom: 8px;
        }
        .signature-place {
            height: 35px;
            border-bottom: 1px solid black;
            margin-bottom: 6px;
        }
        .signature-hint {
            font-size: 12px;
            color: #555;
        }
        .stamp {
            text-align: center;
            font-family: 'Courier New';
            font-size: 12px;
            margin-top: 20px;
            border-top: 1px dashed #aaa;
            padding-top: 15px;
        }
        button.print-btn {
            margin: 20px auto;
            display: block;
            padding: 8px 20px;
            background: #0a3e6d;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        @media print {
            body { background: white; }
            button.print-btn { display: none; }
            .print-area { box-shadow: none; }
        }
    </style>
</head>
<body>
<div class="print-area">
    <div class="header">
        <div class="org-name">${safe.company}</div>
        <div class="doc-title">РАЗОВЫЙ ПРОПУСК</div>
    </div>
    <div class="info-row"><span class="info-label">№ пропуска:</span> <span class="info-value">VIS-${safe.id}</span></div>
    <div class="info-row"><span class="info-label">ФИО посетителя:</span> <span class="info-value">${safe.full_name}</span></div>
    <div class="info-row"><span class="info-label">Компания:</span> <span class="info-value">${safe.company}</span></div>
    <div class="info-row"><span class="info-label">К кому прибыл:</span> <span class="info-value">${safe.whom_visit}</span></div>
    <div class="info-row"><span class="info-label">Цель визита:</span> <span class="info-value">${safe.purpose}</span></div>
    <div class="info-row"><span class="info-label">Дата и время прибытия:</span> <span class="info-value">${checkInDate}</span></div>
    <div class="footer">
        <div class="footer-row">
            <div class="signature-block">
                <div class="signature-label">Пропуск выдан сотрудником:</div>
                <div class="signature-place"></div>
                <div class="signature-hint">(фамилия, инициалы)</div>
            </div>
            <div class="signature-block">
                <div class="signature-label">Подпись сотрудника:</div>
                <div class="signature-place"></div>
                <div class="signature-hint">(подпись)</div>
            </div>
        </div>
        <div class="stamp">МЕСТО ДЛЯ ПЕЧАТИ<br>(Организация)</div>
    </div>
</div>
<button class="print-btn" onclick="window.print()">🖨️ Распечатать пропуск</button>
</body>
</html>`);
    passWindow.document.close();
}