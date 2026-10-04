package main
import("fmt";"os";"os/exec";"path/filepath")
func cmdWatchdog(args []string) error {
 if len(args)==0 || wantsHelp(args) {fmt.Println("Usage: stavka watchdog start|stop|status|tick|run|test|arm|disarm --config PATH\nRead-only five-minute Studio supervision; no automatic creative dispatch until accepted plan. Lifecycle changes emit CLI events.");return nil}
 exe,err:=os.Executable();if err!=nil{return err};script:=filepath.Join(filepath.Dir(exe),"watchdog.py")
 if args[0]=="start" || args[0]=="stop" || args[0]=="arm" || args[0]=="disarm" {recordCliEventWithCID("watchdog-"+args[0],"codex-wap1","studio","","Studio sprint watchdog lifecycle",correlationID("watchdog"))}
 python:=os.Getenv("STAVKA_WATCHDOG_PYTHON");if python=="" {python="python3"}
 cmd:=exec.Command(python,append([]string{script},args...)...);cmd.Stdout=os.Stdout;cmd.Stderr=os.Stderr;return cmd.Run()
}
