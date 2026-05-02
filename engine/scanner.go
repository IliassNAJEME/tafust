package main

import (
	"encoding/json"
	"fmt"
)

// Résultat simple pour test d'interopérabilité
type Result struct {
	Message string `json:"message"`
	Status  string `json:"status"`
}

func main() {
	res := Result{
		Message: "Go Backend Active",
		Status:  "OK",
	}
	
	output, _ := json.Marshal(res)
	fmt.Println(string(output))
}
