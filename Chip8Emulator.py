import time
import sys
import random
import os
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
from tkinter import *
from tkinter import filedialog

#defining entry point for opcodes in the rom
ProgramCounter = 0x200
#defining necessary global values for board,delaytimer and soundtimer
board = []
delayTimer = 0
soundTimer  = 0
#Main memeory and stack used by chip 8
Memory = []


def browseFiles():
    filename = filedialog.askopenfilename(initialdir = ".",
                                          title = "Select a Rom",
                                          filetypes = (("Chip8 files",
                                                        "*.ch8*"),
                                                       ("all files",
                                                        "*.*")))
    return filename

#Stack commands
def pushMemory(value):
#Add a value to the bottom of the stack memory
        return Memory.append(value)
    
def popMemory():
#Return the value at the top of the stack memory
        return Memory.pop()

#Class to define the structure of register memories on the chip 8 and methods that can be performed on them
class Register:
    def __init__(self, bits):
        self.value = 0
        self.bits = bits

    def checkCarry(self):
        hexValue = hex(self.value)[2:]

        if len(hexValue) > self.bits / 4:
            self.value = int(hexValue[-int(self.bits / 4):], 16)
            return 1
        
        return 0
    
    def checkBorrow(self):
        if self.value < 0:
            self.value = abs(self.value)
            return 0
        
        return 1
    
    def readValue(self):
        return hex(self.value)
    
    def setValue(self, value):
        self.value = value

#Creating the stack memory and making it the size of a chip 8 rom
Memory = []
for i in range(0, 4096):
    Memory.append(0x0)
            
#defineing fonts for roms that that use numbers and letters
FontSet = [0xF0, 0x90, 0x90, 0x90, 0xF0,0x20, 0x60, 0x20, 0x20, 0x70,0xF0, 0x10, 0xF0, 0x80, 0xF0,0xF0, 0x10, 0xF0, 0x10, 0xF0,0x90, 0x90, 0xF0, 0x10, 0x10,0xF0, 0x80, 0xF0, 0x10, 0xF0,0xF0, 0x80, 0xF0, 0x90, 0xF0,0xF0, 0x10, 0x20, 0x40, 0x40, 0xF0, 0x90, 0xF0, 0x90, 0xF0, 0xF0, 0x90, 0xF0, 0x10, 0xF0, 0xF0, 0x90, 0xF0, 0x90, 0x90, 0xE0, 0x90, 0xE0, 0x90, 0xE0, 0xF0, 0x80, 0x80, 0x80, 0xF0, 0xE0, 0x90, 0x90, 0x90, 0xE0,0xF0, 0x80, 0xF0, 0x80, 0xF0, 0xF0, 0x80, 0xF0, 0x80, 0x80  ]

        
for i in range(len(FontSet)):
    Memory[i] = FontSet[i]

#Creating an array that will store chip 8 register memeories
Registers = []
for i in range(16):
    Registers.append(Register(8))        
RegisterI = Register(16)

#initialize pygame and create delayTimer 
pygame.init()
pygame.time.set_timer(pygame.USEREVENT+1, int(1000 / 60))

#defining commands to be translated from keyboard inputs to chip 8 16 commands       
keys = []
for i in range(0, 16):
    keys.append(False)
keyDict = {49 : 1,50 : 2,51 : 3,52 : 0xc,113 : 4,119 : 5,101 : 6,114 : 0xd,97 : 7,115 : 8,100 : 9,102 : 0xe,122 : 0xa,120 : 0,99 : 0xb,118 : 0xf}

#Defining board and background for the pygame
board = []
for i in range(32):
    line = []
    for j in range(64):
        line.append(0)
    board.append(line)
emptyboard = board[:]

#pygame config
size = 10
screen = pygame.display.set_mode([64 * size,  32 * size])
screen.fill([0, 255, 51])
pygame.display.flip()
#pygame window name
pygame.display.set_caption('Chip-8 Emulator')



#opcode commands and thier description    
def opcode(hexString):
        global ProgramCounter
        global board
        global Registers
        global isKeyDown
        global delayTimer
        global soundTimer
#----------Call opcode
        if hexString[0] == '0':

            if hexString[1] != '0':
                #CALL RCA 1802 machine languageat address
                print("This is not chip8 code, there is RCA 1802 code at" + hexString[1:] + '>')
                #Execute machine language subroutine at address
            else:
#----------display opcode
                if hexString == '00e0':
                    #CLS
                    #Clear screen
                    PixelOff()

#----------Flow opcode
                elif hexString == '00ee':
                    #RET
                    ProgramCounter = popMemory()        
        elif hexString[0] == '1':
            #jp
            #jump to adddress given
            ProgramCounter = int(hexString[1:], 16) - 2
        
        elif hexString[0] == '2':
            #CALL NNN
            pushMemory(ProgramCounter)
            ProgramCounter = int(hexString[1:], 16) - 2

#----------Conditional opcode        
        elif hexString[0] == '3':
            #SE VX, NN
            VX = int(hexString[1], 16)
            NN = int(hexString[2:], 16)            
            #Skip the next instruction if register VX is equal to NN
            if Registers[VX].value == NN:
                ProgramCounter += 2

        elif hexString[0] == '4':
            #SNE VX, NN
            VX = int(hexString[1], 16)
            NN = int(hexString[2:], 16)            
            #Skip the next instruction if register VX is not equal to NN.
            if Registers[VX].value != NN:
                ProgramCounter += 2

        elif hexString[0] == '5':
            #SE VX, VY
            VX = int(hexString[1], 16)
            VY = int(hexString[2], 16)            
            #Skip the next instruction if register VX equals VY.
            if Registers[VX].value == Registers[VY].value:
                ProgramCounter += 2
                
#----------constant opcode
        elif hexString[0] == '6':
            #LD VX, NN
            NN = int(hexString[1], 16)
            VX = int(hexString[2:], 16)
            #Load immediate value NN into register VX.
            Registers[NN].value = VX
        
        elif hexString[0] == '7':
            #ADD VX, NN
            NN = int(hexString[1], 16)
            VF = int(hexString[2:], 16)
            #Add immediate value NN to register VX. Does not effect VF.
            Registers[NN].value += VF
            Registers[NN].checkCarry()

#----------Assign opcode        
        elif hexString[0] == '8':
            if hexString[3] == '0':
                #LD Vx, Vy
                #Store the value of register VY in register VX
                VY= int(hexString[1], 16)
                VX = int(hexString[2], 16)

                Registers[VY].value = Registers[VX].value
                
#----------Bitop opcodes            
            elif hexString[3] == '1':
                #OR Vx, Vy
                #Set Vx = Vx OR Vy.
                Vx = int(hexString[1], 16)
                Vy = int(hexString[2], 16)

                Registers[Vx].value = Registers[Vx].value | Registers[Vy].value
            
            elif hexString[3] == '2':
                #AND Vx, Vy
                #Set Vx = Vx AND Vy.
                Vx = int(hexString[1], 16)
                Vy = int(hexString[2], 16)

                Registers[Vx].value = Registers[Vx].value & Registers[Vy].value
            
            elif hexString[3] == '3':
                #XOR Vx, Vy
                #Set Vx = Vx XOR Vy.
                Vx = int(hexString[1], 16)
                Vy = int(hexString[2], 16)

                Registers[Vx].value = Registers[Vx].value ^ Registers[Vy].value

#----------Math opcodes            
            elif hexString[3] == '4':
                #ADD Vx, Vy
                #Set Vx = Vx + Vy, set VF = carry
                Vx = int(hexString[1], 16)
                Vy = int(hexString[2], 16)

                Registers[Vx].value += Registers[Vy].value

                Registers[0xf].value = Registers[Vx].checkCarry()
            
            elif hexString[3] == '5':
                #SUB Vx, Vy
                #Set Vx = Vx - Vy, set VF = NOT borrow
                Vx = int(hexString[1], 16)
                Vy = int(hexString[2], 16)

                Registers[Vx].value -= Registers[Vy].value

                Registers[0xf].value = Registers[Vx].checkBorrow()


#----------BitOp opcodes             
            elif hexString[3] == '6':
                #SHR Vx {Vy}
                #Set Vx = Vx SHR 1.
                Vx = int(hexString[1], 16)
                Vy = int(bin(Registers[Vx].value)[-1])

                Registers[Vx].value = Registers[Vx].value >> 1
                Registers[0xf].value = Vy

#----------Math opcodes            
            elif hexString[3] == '7':
                #SUBN Vx, Vy
                #Set Vx = Vy - Vx
                Vx = int(hexString[1], 16)
                Vy = int(hexString[2], 16)

                Registers[Vx].value = Registers[Vy].value - Registers[Vx].value

                Registers[0xf].value = Registers[Vx].checkBorrow()

#----------BitOp opcode
            elif hexString[3] == 'e':
                #SHL Vx {Vy} 
                #Set Vx = Vx SHL 1
                Vx = int(hexString[1], 16)
                Vy = int(bin(Registers[Vx].value)[2])

                Registers[Vx].value = Registers[Vx].value << 1
                Registers[0xf].value = Vy
                
#----------Conditional opcode
        elif hexString[0] == '9':
            #SNE Vx, Vy
            #Skip next instruction if Vx != Vy.
            Vx = int(hexString[1], 16)
            Vy = int(hexString[2], 16)

            if Registers[Vx].value != Registers[Vy].value:
                ProgramCounter += 2


#----------Memory opcode        
        elif hexString[0] == 'a':
            #LD I, addr
            #Set I = NNN
            addr = int(hexString[1:], 16)

            RegisterI.value = addr


#----------Flow opcode        
        elif hexString[0] == 'b':
            #JP V0
            #The program counter is set to address
            addr = int(hexString[1:], 16)
            ProgramCounter = Registers[0].value + addr - 2

#----------Random opcode  
        elif hexString[0] == 'c':
            #RND Vx, byte
            #Sets VX to the result of a bitwise and operation on a random number from 0 to 255
            VX = int(hexString[1], 16)
            var1 = int(hexString[2:], 16)

            randVar = random.randint(0, 255)

            Registers[VX].value = var1 & randVar

#----------Display opcode        
        elif hexString[0] == 'd':
            #Dxyn - DRW Vx, Vy, nibble
            #Display n-byte sprite starting at memory location I at (Vx, Vy)
            Vx = int(hexString[1], 16)
            Vy = int(hexString[2], 16)
            N  = int(hexString[3], 16)

            addr = RegisterI.value
            sprite = Memory[addr: addr + N]
            for i in range(len(sprite)):
                if type(sprite[i]) == str:
                     sprite[i] = int(sprite[i], 16)

            if draw(Registers[Vx].value, Registers[Vy].value, sprite):
                Registers[0xf].value = 1
            else:
                Registers[0xf].value = 0

                
#----------Keyboard command opcode
        elif hexString[0] == 'e':
            if hexString[2:] == '9e':
                #SKP Vx
                #Skip next instruction if key with the value of Vx is pressed.
                Vx = int(hexString[1], 16)
                key = Registers[Vx].value
                if keys[key]:
                    ProgramCounter += 2

            elif hexString[2:] == 'a1':
                #SKNP Vx
                #Skip next instruction if key with the value of Vx is not pressed
                Vx = int(hexString[1], 16)
                key = Registers[Vx].value
                if not keys[key]:
                    ProgramCounter += 2
                    
#----------delayTimer and sound delayTimer opcode    
        elif hexString[0] == 'f':
            if hexString[2:] == '07':
                #LD Vx, DT
                #Set Vx = delay timer value
                Vx = int(hexString[1], 16)
                Registers[Vx].value = delayTimer 


#----------Keyboard command opcode
            elif hexString[2:] == '0a':
                #LD Vx, K
                #Wait for a key press, store the value of the key in Vx
                Vx = int(hexString[1], 16)
                key = None

                while True:
                    keyboard()
                    isKeyDown = False

                    for i in range(len(keys)):
                        if keys[i]:
                            key = i
                            isKeyDown = True
                    
                    if isKeyDown:
                        break
                
                Registers[Vx].value = key


#----------delayTimer and sound delayTimer opcode
            elif hexString[2:] == '15':
                #LD DT, Vx
                #Set delay timer = Vx.
                Vx = int(hexString[1], 16)
                value = Registers[Vx].value

                delayTimer = value
            
            elif hexString[2:] == '18':
                #LD ST, Vx
                #Set sound timer = Vx.
                Vx = int(hexString[1], 16)
                value = Registers[Vx].value

                soundTimer= value

#----------Memory opcode            
            elif hexString[2:] == '1e':
                #ADD I, Vx
                #Set I = I + Vx.
                Vx = int(hexString[1], 16)
                RegisterI.value += Registers[Vx].value
            
            elif hexString[2:] == '29':
                #LD F, Vx
                #Set I = location of sprite for digit Vx.
                Vx = int(hexString[1], 16)
                value = Registers[Vx].value

                RegisterI.value = value * 5

#----------binary-coded decimal opcode            
            elif hexString[2:] == '33':
                #LD B, Vx
                #Store BCD representation of Vx in memory locations I, I+1, and I+2.
                Vx = int(hexString[1], 16)
                value = str(Registers[Vx].value)

                fillNum = 3 - len(value)
                value = '0' * fillNum + value

                for i in range(len(value)):
                    Memory[RegisterI.value + i] = int(value[i])

#----------Memory opcode            
            elif hexString[2:] == '55':
                #LD [I], Vx
                #Store registers V0 through Vx in memory starting at location I.                
                Vx = int(hexString[1], 16)
                for i in range(0, Vx + 1):
                    Memory[RegisterI.value + i] = Registers[i].value

            elif hexString[2:] == '65':
                #LD Vx, [I]
                #Read registers V0 through Vx from memory starting at location I.
                Vx = int(hexString[1], 16)
                for i in range(0, Vx + 1):
                    Registers[i].value = Memory[RegisterI.value + i]

        ProgramCounter += 2

#Read rom to create initial board
def draw(Vx, Vy, sprite):
        collision = False

        spriteBits = []
        for i in sprite:
            binary = bin(i)
            line = list(binary[2:])
            fillNum = 8 - len(line)
            line = ['0'] * fillNum + line

            spriteBits.append(line)

        for i in range(len(spriteBits)):
            for j in range(8):
                try:
                    if board[Vy + i][Vx + j] == 1 and int(spriteBits[i][j]) == 1:
                        collision = True

                    board[Vy + i][Vx + j] = board[Vy + i][Vx + j] ^ int(spriteBits[i][j])
                except:
                    continue
        
        return collision
    
#sound tone   
def sound():
    global delayTimer
    if delayTimer  > 1:
            os.system('play --no-show-progress --null --channels 1 synth %s triangle %f' % (delayTimer / 60, 440))
            delayTimer  = 0
            
#clear screen    
def PixelOff():
        global board
        board = [[0 for _ in row] for row in board]

#Translate hex rom, define entry point and append to stack memory        
def inputRom():
        global Memory
        rom = []

        filename = browseFiles()
                                          
        if filename == "":
            quit()
      
        with open(filename, 'rb') as f:
            wholeProgram = f.read()

            for i in wholeProgram:
                hexString = i
                rom.append(hexString)

        
        offset = int('0x200', 16)
        for i in rom:
            Memory[offset] = i
            offset += 1

#Convert value to hex
def hexConvert(Num):
        newHex = hex(Num)[2:]
        if len(newHex) == 1:
            newHex = '0' + newHex
        
        return newHex

#Translate keyboard inputs to chip8 commands
def keyboard():
        global keys
        global keyDict
        global delayTimer
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.USEREVENT+1:
                if delayTimer > 0:
                    delayTimer = delayTimer - 1

            elif event.type == pygame.KEYDOWN:
                try:
                    targetKey = keyDict[event.key]
                    keys[targetKey] = True

                except: pass

            elif event.type == pygame.KEYUP:
                try:
                    targetKey = keyDict[event.key]
                    keys[targetKey] = False

                except: pass
                
#Create board
def pixels():
        for i in range(0, len(board)):
            for j in range(0, len(board[0])):
                cellColor = [0, 0, 0]

                if board[i][j] == 1:
                    cellColor = [0, 255, 51]
                
                pygame.draw.rect(screen, cellColor, [j * size, i * size, size, size], 0)
        
        pygame.display.flip()
        
#insert rom
inputRom()

#run game
clock = pygame.time.Clock()
while True:
            clock.tick(300)
            keyboard()
            sound()
            opcode(hexConvert(Memory[ProgramCounter])+hexConvert(Memory[ProgramCounter + 1]))
            pixels()
