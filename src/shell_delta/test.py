import tkinter

tcl = tkinter.Tcl()

# テスト用のTcl関数をいくつか定義してみる
tcl.eval("""
proc test1 {} { return "hello" }
proc test2 {a b} { return [expr {$a + $b}] }
proc my_custom_func {} { return 123 }
""")

# 1. 読み込まれているすべての関数（proc）一覧を取得
# info procs の実行結果はTclのリスト形式で返ってくるため、split() でPythonのリストに変換
all_procs = tcl.eval("info procs").split()

print("読み込まれている関数一覧:")
print(all_procs)
# 出力例: ['test1', 'test2', 'my_custom_func', '<x>', ...]
