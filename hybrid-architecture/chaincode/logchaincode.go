package main

import (
	"fmt"
	"github.com/hyperledger/fabric-contract-api-go/contractapi"
)

// SmartContract provides functions for managing a log hash
type SmartContract struct {
	contractapi.Contract
}

// CreateLogHash issues a new log hash to the world state with given details.
func (s *SmartContract) CreateLogHash(ctx contractapi.TransactionContextInterface, logId string, logHash string) error {
	// Check if the log ID already exists
	exists, err := s.LogHashExists(ctx, logId)
	if err != nil {
		return err
	}
	if exists {
		return fmt.Errorf("the log %s already exists", logId)
	}

	// Armazena diretamente o hash do log no estado mundial, usando o logId como chave.
	// A variável 'log' que não era usada foi removida.
	return ctx.GetStub().PutState(logId, []byte(logHash))
}

// QueryLogHash returns the log hash stored in the world state with given id.
func (s *SmartContract) QueryLogHash(ctx contractapi.TransactionContextInterface, logId string) (string, error) {
	logHashBytes, err := ctx.GetStub().GetState(logId)
	if err != nil {
		return "", fmt.Errorf("failed to read from world state: %v", err)
	}
	if logHashBytes == nil {
		return "", fmt.Errorf("the log %s does not exist", logId)
	}

	return string(logHashBytes), nil
}

// LogHashExists returns true when log with given ID exists in world state
func (s *SmartContract) LogHashExists(ctx contractapi.TransactionContextInterface, logId string) (bool, error) {
	logHashBytes, err := ctx.GetStub().GetState(logId)
	if err != nil {
		return false, fmt.Errorf("failed to read from world state: %v", err)
	}

	return logHashBytes != nil, nil
}


func main() {
	chaincode, err := contractapi.NewChaincode(&SmartContract{})
	if err != nil {
		fmt.Printf("Error creating loghash chaincode: %v", err)
		return
	}

	if err := chaincode.Start(); err != nil {
		fmt.Printf("Error starting loghash chaincode: %v", err)
	}
}