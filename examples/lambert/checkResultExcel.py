from openpyxl import Workbook

def check_result_excel():
    with open("Requirement AI Check Result-CLOUD.md","r",encoding='utf-8') as f:
        wb = Workbook()
        ws = wb.active
        headers = ['Backlog', 'Who', 'What', 'Where', 'When', 'Why', 'How']
        ws.append(headers)
        while True:
            data = []

            while len(data) < 7:
                line = f.readline()
                if not line:
                    # 保存工作簿
                    wb.save("example3.xlsx")
                    return

                if "###" in str(line) and "5W1H" not in str(line):
                    backlog = str(line).replace("### ","").replace("\n","")
                    data.append(backlog)
                    continue

                if str(line).startswith("-") and "Who" in str(line) and "Missing" in str(line):
                    data.append(0)
                    continue
                if str(line).startswith("-") and "Who" in str(line) and "Missing" not in str(line):
                    data.append(1)
                    continue

                if str(line).startswith("-") and "What" in str(line) and "Missing" in str(line):
                    data.append(0)
                    continue
                if str(line).startswith("-") and "What" in str(line) and "Missing" not in str(line):
                    data.append(1)
                    continue

                if str(line).startswith("-") and "Where" in str(line) and "Missing" in str(line):
                    data.append(0)
                    continue
                if str(line).startswith("-") and "Where" in str(line) and "Missing" not in str(line):
                    data.append(1)
                    continue

                if str(line).startswith("-") and "When" in str(line) and "Missing" in str(line):
                    data.append(0)
                    continue
                if str(line).startswith("-") and "When" in str(line) and "Missing" not in str(line):
                    data.append(1)
                    continue

                if str(line).startswith("-") and "Why" in str(line) and "Missing" in str(line):
                    data.append(0)
                    continue
                if str(line).startswith("-") and "Why" in str(line) and "Missing" not in str(line):
                    data.append(1)
                    continue

                if str(line).startswith("-") and "How" in str(line) and "Missing" in str(line):
                    data.append(0)
                    break
                if str(line).startswith("-") and "How" in str(line) and "Missing" not in str(line):
                    data.append(1)
                    break

                if len(data)>0 and isinstance(data[0], int):
                    break

            if len(data) == 7:
                ws.append(data)
                print(data)



check_result_excel()