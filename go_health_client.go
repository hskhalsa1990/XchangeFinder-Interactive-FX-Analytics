package main
import ("fmt"; "net/http")
func main(){ r,err:=http.Get("http://127.0.0.1:8000/health"); if err!=nil { panic(err) }; defer r.Body.Close(); fmt.Println("API status:",r.Status) }
