"""MySQL CLI 导入、关联及导出。密码仅从环境变量读取，不写入代码或日志。"""
import argparse, csv, io, json, os, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def execute(sql, args):
    cmd = [args.mysql, '--default-character-set=utf8mb4', '--batch', '--raw', '--local-infile=1']
    if args.login_path:
        cmd.insert(1, '--login-path='+args.login_path)
    else:
        cmd += ['-h', args.host, '-P', str(args.port), '-u', args.user]
    result = subprocess.run(cmd, input=sql, text=True, encoding='utf-8',
                            capture_output=True, env=os.environ.copy())
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--raw-dir',type=Path,required=True)
    p.add_argument('--mysql',default=r'C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe')
    p.add_argument('--host',default='localhost'); p.add_argument('--port',default=3306,type=int)
    p.add_argument('--user',default='root'); p.add_argument('--login-path')
    p.add_argument('--extract-only',action='store_true')
    args=p.parse_args()
    if not args.extract_only:
        check=execute("SELECT COUNT(*) AS n FROM information_schema.tables WHERE table_schema='user_growth_portfolio' AND table_name LIKE 'raw_%';",args)
        if int(check.strip().splitlines()[-1]):
            counts=execute('SELECT (SELECT COUNT(*) FROM user_growth_portfolio.raw_visits)+(SELECT COUNT(*) FROM user_growth_portfolio.raw_orders)+(SELECT COUNT(*) FROM user_growth_portfolio.raw_costs) AS n;',args)
            if int(counts.strip().splitlines()[-1]):
                raise RuntimeError('原始表已有数据。核实后使用 --extract-only；不自动清空数据。')
        enabled=execute('SELECT @@GLOBAL.local_infile AS enabled;',args).strip().splitlines()[-1]
        changed=enabled=='0'
        try:
            if changed: execute('SET GLOBAL local_infile=ON;',args)
            sql=(ROOT/'sql/01_import.sql').read_text(encoding='utf-8')
            execute(sql.replace('${RAW_DIR}',args.raw_dir.resolve().as_posix().replace("'","''")),args)
        finally:
            if changed: execute('SET GLOBAL local_infile=OFF;',args)
    execute((ROOT/'sql/02_extract.sql').read_text(encoding='utf-8'),args)
    out=ROOT/'data/mysql_extract'; out.mkdir(parents=True,exist_ok=True)
    for name in ['visits','orders','costs','user_acquisition']:
        result=execute('SELECT * FROM user_growth_portfolio.v_'+name+';',args)
        rows=csv.reader(io.StringIO(result),delimiter='\t')
        with (out/(name+'.csv')).open('w',encoding='utf-8',newline='') as f:
            writer=csv.writer(f)
            for row in rows: writer.writerow(['' if x=='NULL' else x for x in row])
    checks=execute((ROOT/'sql/03_validation.sql').read_text(encoding='utf-8'),args)
    (ROOT/'reports/mysql_validation.txt').write_text(checks,encoding='utf-8')
    meta={'engine':execute('SELECT VERSION();',args).strip().splitlines()[-1],
          'raw_dir':str(args.raw_dir.resolve()),'source':'MySQL CLI actual execution',
          'database':'user_growth_portfolio'}
    (ROOT/'reports/mysql_execution.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print('MySQL import/extract complete:',out)

if __name__=='__main__': main()
