10.9日改动
与先前的电商项目做了对比，发现环境变量的设置方面还有优化的地方，可以将修改环境变量的命令行改动为输入关键词就可以修改设置的全部环境变量

优点：方便，牵一发而动全身
缺点：一改就要一起改，没办法做到只改某一个

扫码下单系统的原有部分
在config.py设置了Config类，
Config类的功能主要为使用os来读取命令行中的环境变量（SET）
实例化config = Config（）
###
用类不够灵活
就是说类因为是整个类import过来的，这个类就在import过来的那一瞬间就被拍下了快照，所以说就是后续整个会话的操作都是在这个快照下的环境进行，然后函数的话就是没调用一次就实行一次，可以获得最新的值，其实类里面的函数也是流动的，但是因为import时只读一遍，就被拍快照了


然后如何定位到模块呢
from config import config
db_helper

用模块函数接收变量
DB_PATH = config.DB_PATH
在连接数据库的时候填入环境变量
conn = sqlite3.connect(DB_PATH, isolation_level=None)

要修改base_url的话也是这样

而修改后的代码
不使用类来将方法囊括，而是分为一个个专门负责各自环境变量读取工作的函数
这样在import进不同的模块中，一调用就会回到config去执行，获得命令行中最新的环境变量


修改后的代码
首先时config全改为函数

然后就是在conftest中将详细的环境变量书写好
request.config.getoption取得命令行中的相关内容
传给这个env，然后再找到匹配的
传给这个config = env_map[env]

最后    for key, value in config.items():
        os.environ[key] = value
去遍历整个环境变量
直接将环境变量全部修改好

然后在运行db_helper时，from app.config import get_db_path
config  的os.getenv()读取到当前conftest环境中的环境变量
将这个值传给db_helper



