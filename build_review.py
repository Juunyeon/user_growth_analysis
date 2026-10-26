"""执行notebook各代码单元并保存真实输出；生成可离线阅读的HTML分析报告。"""
import contextlib,io,json,os,platform,sys,uuid
from pathlib import Path
import html
import pandas as pd
import numpy as np

ROOT=Path(__file__).resolve().parents[1]

def main():
    cells=[];scope={};execution=0
    def md(s):cells.append({'cell_type':'markdown','id':uuid.uuid4().hex[:8],'metadata':{},'source':s.splitlines(keepends=True)})
    def code(s):
        nonlocal execution
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):exec(compile(s,'<notebook>','exec'),scope)
        execution+=1
        outputs=[{'output_type':'stream','name':'stdout','text':stream.getvalue().splitlines(keepends=True)}] if stream.getvalue() else []
        cells.append({'cell_type':'code','id':uuid.uuid4().hex[:8],'metadata':{},'source':s.splitlines(keepends=True),'execution_count':execution,'outputs':outputs})
    md('# 用户增长分析：MySQL → Python\n\n原始数据为 visits / orders / costs。先完成SQL导入与关联，再运行以下代码。所有输出为本次实际执行。完整公式与边界见 reports/metric_dictionary.md。Excel展示及完整项目报告见项目README。')
    code("from pathlib import Path\nimport sys, json\nimport pandas as pd\nroot = Path.cwd()\nif (root / 'analyze.py').exists(): root = root.parent\nelif not (root / 'python/analyze.py').exists():\n    root = root / 'outputs/user_growth_analysis'\nassert (root / 'python/analyze.py').exists(), '请在项目根目录或python目录打开notebook'\nsys.path.insert(0, str(root / 'python'))\nfrom analyze import main\nresults = main()\n")
    md('## 1. 清理与关联校验\n\nUID以字符串读取；两条异常时长置空，保留合法开始时间；窗口外订单排除。SQL和Python分别聚合收入并逐用户核对。')
    code("print(json.dumps(results['audit'], ensure_ascii=False, indent=2))")
    md('## 2. 新增、活跃与黏性\n\n新增是观察期首访；WAU/MAU是滚动窗口，自然月MAU单列。起始不完整窗口不用于完整窗口均值。')
    code("print(results['monthly'].to_string())\nprint(results['daily'].tail(7).to_string())")
    md('![月新增与活跃](../figures/02_monthly_growth.svg)\n\n![用户黏性](../figures/04_stickiness.svg)')
    md('## 3. 留存与同期群\n\n严格第1/7/30个自然日回访，不是期间任意回访；未成熟分母排除。月cohort空白是未观察。')
    code("print(results['retention'].tail(5).to_string(index=False))\nprint(results['cohort'].to_string())")
    md('![留存](../figures/05_retention.svg)\n\n![月同期群](../figures/06_cohort.svg)')
    md('## 4. 生命周期\n\n月末两个相邻30日窗口划分新访客、持续活跃、沉默、回流；四类互斥，合计等于已知用户。')
    code("print(results['lifecycle'].to_string())")
    md('![生命周期](../figures/07_lifecycle.svg)')
    md('## 5. 首访到首购\n\n以1/7/30×24小时为固定窗口，只比较完整观察用户。成功购买者的首购时长不能推断全部用户。')
    code("print(results['conversion'].to_string(index=False))")
    md('![固定窗口转化](../figures/08_conversion.svg)')
    md('## 6. 渠道、CAC与收入LTV\n\n首次触点唯一归因；渠道6/7费用缺失不填0。固定30日LTV仅对整月成熟的首访月份显示。ROAS不是利润ROI。')
    code("print(results['channel'].to_string())\nprint(results['ltv30'].query('fully_mature_30d').head(18).to_string(index=False))")
    md('![渠道CAC](../figures/09_channel_cac.svg)\n\n![渠道ROAS](../figures/10_channel_roas.svg)\n\nExcel展示及完整Word报告见项目README；本notebook保留MySQL与Python指标及核查结果。')
    nb={'cells':cells,'metadata':{'kernelspec':{'display_name':'Python 3','language':'python','name':'python3'},'language_info':{'name':'python','version':platform.python_version()}},'nbformat':4,'nbformat_minor':5}
    (ROOT/'python/user_growth_analysis.ipynb').write_text(json.dumps(nb,ensure_ascii=False,indent=1),encoding='utf-8')
    (ROOT/'requirements.txt').write_text(f'pandas=={pd.__version__}\nnumpy=={np.__version__}\n',encoding='utf-8')
    (ROOT/'reports/environment.json').write_text(json.dumps({'python':sys.version,'executable':sys.executable,'pandas':pd.__version__,'numpy':np.__version__},ensure_ascii=False,indent=2),encoding='utf-8')
    report=(ROOT/'reports/analysis_report.md').read_text(encoding='utf-8')
    # HTML报告嵌入SVG与表格，脱离项目目录也可阅读。
    parts=['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>用户增长分析报告</title><style>body{font:16px/1.8 "Microsoft YaHei",sans-serif;color:#243249;background:#f4f7fb;margin:0}main{max-width:1150px;margin:auto;padding:40px;background:white}h1,h2{color:#15366e}p{margin:12px 0}table{border-collapse:collapse;font-size:14px;width:100%;margin:20px 0}td,th{border:1px solid #dce4ef;padding:6px;text-align:right}th{background:#edf4ff}svg{width:100%;height:auto;border:1px solid #dce4ef;margin:20px 0}.note{color:#64748b}</style><main>']
    table=[]
    def flush():
        if not table:return
        parts.append('<table>')
        for i,line in enumerate(table):
            if i==1:continue
            tag='th' if i==0 else 'td'
            parts.append('<tr>'+''.join(f'<{tag}>{html.escape(x.strip())}</{tag}>' for x in line.strip('|').split('|'))+'</tr>')
        parts.append('</table>');table.clear()
    for line in report.splitlines():
        if line.startswith('|'):table.append(line);continue
        flush()
        if line.startswith('# '):parts.append('<h1>'+html.escape(line[2:])+'</h1>')
        elif line.startswith('## '):parts.append('<h2>'+html.escape(line[3:])+'</h2>')
        elif line.strip():parts.append('<p>'+html.escape(line)+'</p>')
    flush();parts.append('<h2>图表与证据</h2>')
    for p in sorted((ROOT/'figures').glob('*.svg')):parts.append(p.read_text(encoding='utf-8'))
    parts.append('</main></html>')
    (ROOT/'reports/analysis_report.html').write_text('\n'.join(parts),encoding='utf-8')
    print('Executed notebook and HTML review report written.')

if __name__=='__main__':
    os.chdir(ROOT)
    main()
