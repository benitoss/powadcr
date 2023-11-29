/* +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    Nombre: TAPproccesor.h
    
    Creado por:
      Copyright (c) Antonio Tamairón. 2023  / https://github.com/hash6iron/powadcr
      @hash6iron / https://powagames.itch.io/
    
    Descripción:
    Conjunto de recursos para la gestión de ficheros .TAP de ZX Spectrum

    Version: 0.2

    Historico de versiones
    ----------------------
    v.0.1 - Version inicial
    v.0.2 - Se han hecho modificaciones relativas al resto de clases para HMI y SDmanager. Se ha incluido la reproducción y analisis de bloques que estaba antes en el powadcr.ino

    Derechos de autor y distribución
    --------------------------------
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
    
    To Contact the dev team you can write to hash6iron@gmail.com
 +++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++*/

#pragma once

// TYPE block
#define HPRGM 0                     //Cabecera PROGRAM
#define HCODE 1                     //Cabecera BYTE  
#define HSCRN 7                     //Cabecera BYTE SCREEN$
#define HARRAYNUM 5                 //Cabecera ARRAY numerico
#define HARRAYCHR 6                 //Cabecera ARRAY char
#define PRGM 2                      //Bloque de datos BASIC
#define SCRN 3                      //Bloque de datos Screen$
#define CODE 4                      //Bloque de datps CM (BYTE)

class TAPproccesor
{

    public:

        // Estructura del descriptor de bloques
        struct tBlockDescriptor 
        {
            bool corrupted = false;
            int offset = 0;
            int size = 0;
            int chk = 0;
            char name[11];
            bool nameDetected = false;
            bool header = false;
            bool screen = false;
            int type = 0;
            char typeName[11];
        };    

        // Estructura tipo TAP
        struct tTAP 
        {
            char name[11];                                  // Nombre del TAP
            int size = 0;                                   // Tamaño
            int numBlocks = 0;                              // Numero de bloques
            tBlockDescriptor* descriptor = NULL;            // Descriptor
        };

    private:
        // Procesador de audio output
        ZXProccesor _zxp;     

        // Gestor de SD
        HMI _hmi;

        // Definicion de un TAP
        tTAP _myTAP;
        SdFat32 _sdf32;
        File32 _mFile;
        int _sizeTAP;
        int _rlen;

        int CURRENT_LOADING_BLOCK = 0;

        // Creamos el contenedor de bloques. Descriptor de bloques
        //tBlockDescriptor* bDscr = new tBlockDescriptor[255];
        // Gestión de bloques
        int _startBlock = 0;
        int _lastStartBlock = 0;

        bool isHeaderTAP(File32 tapFileName)
        {
            bool rtn = false;

            if (tapFileName != 0)
            {
                SerialHW.println("");
                SerialHW.println("");
                SerialHW.println("Begin isHeaderTAP");

                // La cabecera son 19 bytes
                byte* bBlock;
                bBlock = allocateByte(19+1);
                bBlock = sdm.readFileRange32(tapFileName,0,19,true);

                SerialHW.println("");
                SerialHW.println("");
                SerialHW.println("Got bBlock");

                // Obtenemos la firma del TAP
                char* signTZXHeader;
                signTZXHeader = allocateChar(3+1);;


                SerialHW.println("");
                SerialHW.println("");
                SerialHW.println("Initialized signTAP Header");

                // Analizamos la cabecera
                // Extraemos el nombre del programa
                for (int n=0;n<3;n++)
                {   
                    signTZXHeader[n] = (byte)bBlock[n];
                    
                    SerialHW.println("");
                    SerialHW.println("");
                    SerialHW.println((int)signTZXHeader[n]);                  
                }

                if (signTZXHeader[0] == 19 && signTZXHeader[1] == 0 && signTZXHeader[2] == 0)
                {
                    SerialHW.println("");
                    SerialHW.println("");
                    SerialHW.println("is TAP ok");
                    rtn = true;
                }
                else
                {
                    rtn = false;
                }

                // Liberamos memoria
                delete [] signTZXHeader;
                signTZXHeader = NULL;

                // Liberamos memoria
                delete [] bBlock;
                bBlock = NULL;

            }
            else
            { 
            rtn = false;
            }

            log("isHeaderTAP OK");
            return rtn;
        }

        bool isFileTAP(File32 tapFileName)
        {
            bool rtn = false;
            char* szName = new char[254 + 1];

            tapFileName.getName(szName,254);
            String fileName = static_cast<String>(szName);

            if (fileName != "")
            {
                fileName.toUpperCase();
                if (fileName.indexOf("TAP") != -1)
                {
                    if (isHeaderTAP(tapFileName))
                    {
                    rtn = true;
                    }
                    else
                    {
                    rtn = false;
                    }
                }
                else
                {
                    rtn = false;
                }
            }
            else
            {
                rtn = false;
            }

            log("IsFileTAP OK");
            return rtn;
        }

        byte calculateChecksum(byte* bBlock, int startByte, int numBytes)
        {
            // Calculamos el checksum de un bloque de bytes
            byte newChk = 0;

            #if LOG>3
            SerialHW.println("");
            SerialHW.println("Block len: ");
            SerialHW.print(sizeof(bBlock)/sizeof(byte*));
            #endif

            // Calculamos el checksum (no se contabiliza el ultimo numero que es precisamente el checksum)
            
            for (int n=startByte;n<(startByte+numBytes);n++)
            {
                newChk = newChk ^ bBlock[n];
            }

            #if LOG>3
            SerialHW.println("");
            SerialHW.println("Checksum: " + String(newChk));
            #endif

            return newChk;
        }


        bool isCorrectHeader(byte* header, int startByte)
        {
            // Verifica que es una cabecera
            bool isHeader = false;
            byte checksum = 0;
            byte calcBlockChk = 0;

            if (header[startByte]==19 && header[startByte+1]==0 && header[startByte+2]==0)
            {
                checksum = header[startByte+20];
                calcBlockChk = calculateChecksum(header,startByte,18);

                if (checksum == calcBlockChk)
                {
                    isHeader = true;
                }
            }

            return isHeader;
        }

        bool isProgramHeader(byte* header, int startByte)
        {
            // Verifica que es una cabecera
            //bool isHeaderPrg = false;
            byte checksum = 0;
            byte calcBlockChk = 0;

            if (isCorrectHeader(header, startByte))
            {
                if (header[startByte+3]==0)
                {
                    checksum = header[startByte+20];
                    calcBlockChk = calculateChecksum(header,startByte,18);

                    if (checksum == calcBlockChk)
                    {
                        //isHeaderPrg = true;
                        return true;
                    }
                }
                else
                //{isHeaderPrg = false;}
                {
                return false;
                }
            }

            //return isHeaderPrg;
            return false;
        }

        int getBlockLen(byte* header, int startByte)
        {
            // Este procedimiento nos devuelve el tamaño definido un bloque de datos
            // analizando los 22 bytes de la cabecera pasada por valor.
            int blockLen = 0;
            if (isCorrectHeader(header,startByte))
            {
                blockLen = (256*header[startByte+22]) + header[startByte+21];
            }
            return blockLen;
        }

        char* getTypeTAPBlock(int nBlock)
        {
            String typeName;
            char* rtnStr = new char[20 + 1];

            switch(nBlock)
            {
                case 0:

                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    typeName = "PROGRAM.HEAD";
                    break;

                case 1:

                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    typeName = "BYTE.DATA";
                    break;

                case 7:

                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    typeName = "SCREEN.HEAD";
                    break;

                case 2:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    typeName = "BASIC BLOCK";
                    break;

                case 3:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    typeName = "SCREEN.DATA";
                    break;

                case 4:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    if (LAST_SIZE != 6914)
                    {
                        typeName = "BYTE.DATA";
                    }
                    else
                    {
                        typeName = "SCREEN.DATA";
                    }
                    break;
            }        

            // Transformamos en char*
            strcpy(rtnStr, typeName.c_str());
            return rtnStr;
        }
        
        char* getNameFromHeader(byte* header, int startByte)
        {
            // Obtenemos el nombre del bloque cabecera      
            char* prgName = new char[10 + 1];

            if (isCorrectHeader(header,startByte))
            {
                // Es una cabecera PROGRAM 
                // el nombre está en los bytes del 4 al 13 (empezando en 0)
                SerialHW.println("");
                SerialHW.println("Name detected ");

                // Extraemos el nombre del programa
                for (int n=4;n<14;n++)
                {   
                    prgName[n-4] = (char)header[n];
                }
            }

            // Pasamos la cadena de caracteres
            return prgName;
        }

        char* getBlockName(char* prgName, byte* header, int startByte)
        {
            // Obtenemos el nombre del bloque cabecera
            // Es una cabecera PROGRAM 
            // el nombre está en los bytes del 4 al 13 (empezando en 0)         
            header[startByte+12] = 0;
            return (char*)(header+2);             
        }
  
        byte* getBlockRange(byte* bBlock, int byteStart, int byteEnd)
        {

            // Extraemos un bloque de bytes indicando el byte inicio y final
            //byte* blockExtracted = new byte[(byteEnd - byteStart)+1];
            byte* blockExtracted = allocateByte((byteEnd - byteStart)+1);

            int i=0;
            for (int n=byteStart;n<(byteStart + (byteEnd - byteStart)+1);n++)
            {
                blockExtracted[i] = bBlock[n];
            }

            return blockExtracted;
        }

        int getNumBlocks(File32 mFile, int sizeTAP)
        {

            int startBlock = 0;
            int lastStartBlock = 0;
            int sizeB = 0;
            int newSizeB = 0;
            int chk = 0;
            int blockChk = 0;
            int numBlocks = 0;

            FILE_CORRUPTED = false;
            
            bool reachEndByte = false;

            int state = 0;    

            //Entonces recorremos el TAP. 
            // La primera cabecera SIEMPRE debe darse.
            SerialHW.println("");
            SerialHW.println("Analyzing TAP file. Please wait ...");
            
            SerialHW.println("");
            SerialHW.println("SIZE TAP: " + String(sizeTAP));

            // Los dos primeros bytes son el tamaño a contar
            sizeB = (256*sdm.readFileRange32(_mFile,startBlock+1,1,false)[0]) + sdm.readFileRange32(_mFile,startBlock,1,false)[0];
            startBlock = 2;

            while(reachEndByte==false)
            {

                byte* tmpRng = allocateByte(sizeB);

                tmpRng = sdm.readFileRange32(_mFile,startBlock,sizeB-1,false);
                chk = calculateChecksum(tmpRng,0,sizeB-1);

                //free(tmpRng);
                delete [] tmpRng;
                tmpRng = NULL;              
                _hmi.getMemFree();
                            
                blockChk = sdm.readFileRange32(_mFile,startBlock+sizeB-1,1,false)[0];
            

                if (blockChk == chk)
                {                                  
                    // Siguiente bloque
                    // Direcion de inicio (offset)
                    startBlock = startBlock + sizeB;
                    // Tamaño
                    newSizeB = (256*sdm.readFileRange32(_mFile,startBlock+1,1,false)[0]) + sdm.readFileRange32(_mFile,startBlock,1,false)[0];

                    numBlocks++;
                    sizeB = newSizeB;
                    startBlock = startBlock + 2;

                    SerialHW.println("");
                    SerialHW.print("OFFSET: 0x");
                    SerialHW.print(startBlock,HEX);
                    SerialHW.print(" / SIZE:   " + String(newSizeB));
                }
                else
                {
                    reachEndByte = true;
                    SerialHW.println("Error in checksum. Block --> " + String(numBlocks) + " - offset: " + String(lastStartBlock));

                    // Abortamos
                    FILE_CORRUPTED = true;
                }

                // ¿Hemos llegado al ultimo byte
                if (startBlock > sizeTAP)                
                {
                    reachEndByte = true;
                    //break;
                    SerialHW.println("");
                    SerialHW.println("Success. End: ");
                }

            }

            return numBlocks;
        }

        bool getInformationOfHead(tBlockDescriptor &tB, int flagByte, int typeBlock, int startBlock, int sizeB, char (&nameTAP)[11])
        {
        
        // Obtenemos informacion de la cabecera

        bool blockNameDetected = false;
        int state = 0;

        if (flagByte < 128)
        {

            // Inicializamos                    
            tB.type = 0;
            strncpy(tB.typeName,"",10);
            
            // Es una CABECERA
            if (typeBlock==0)
            {
                // Es un header PROGRAM

                tB.header = true;
                tB.type = HPRGM;

                blockNameDetected = true;

                // Almacenamos el nombre
                //getBlockName(tB.name,sdm.readFileRange32(_mFile,startBlock,19,false),0);
                strncpy(tB.name,getBlockName(tB.name,sdm.readFileRange32(_mFile,startBlock,19,false),0),10);



                //Cogemos el nombre del TAP de la primera cabecera
                if (startBlock < 23)
                {
                    //nameTAP = (String)bDscr[numBlocks].name;
                    //nameTAP = bDscr[numBlocks].name;
                    strncpy(nameTAP,tB.name,10);
                }

                state = 1;
            }
            else if (typeBlock==1)
            {
                // Array num header
                // Almacenamos el nombre
                strncpy(tB.name,getBlockName(tB.name,sdm.readFileRange32(_mFile,startBlock,19,false),0),10);
                tB.type = HARRAYNUM;    

            }
            else if (typeBlock==2)
            {
                // Array char header
                // Almacenamos el nombre
                strncpy(tB.name,getBlockName(tB.name,sdm.readFileRange32(_mFile,startBlock,19,false),0),10);
                tB.type = HARRAYCHR;    

            }
            else if (typeBlock==3)
            {
                // Byte block

                // Vemos si es una cabecera de una SCREEN
                // para ello temporalmente vemos el tamaño del bloque de codigo. Si es 6914 bytes (incluido el checksum y el flag - 6912 + 2 bytes)
                // es una pantalla SCREEN
                blockNameDetected = true;
                
                // Almacenamos el nombre
                strncpy(tB.name,getBlockName(tB.name,sdm.readFileRange32(_mFile,startBlock,19,false),0),10);

                int tmpSizeBlock = (256*sdm.readFileRange32(_mFile,startBlock + sizeB+1,1,false)[0]) + sdm.readFileRange32(_mFile,startBlock + sizeB,1,false)[0];

                if (tmpSizeBlock == 6914)
                {
                    // Es una cabecera de un Screen
                    tB.screen = true;
                    tB.type = HSCRN;                              

                    state = 2;
                }
                else
                {               
                    tB.type = HCODE;    
                }
        
            }

        }
        else
        {
            if (state == 1)
            {
                state = 0;
                // Es un bloque BASIC                         
                tB.type = PRGM;
            }
            else if (state == 2)
            {
                state = 0;
                // Es un bloque SCREEN                     
                tB.type = SCRN;                         
            }
            else
            {
                // Es un bloque CM                        
                tB.type = CODE;                         
            }
        }   

        return blockNameDetected;     
        }

        void getBlockDescriptor(File32 mFile, int sizeTAP)
        {
            // Para ello tenemos que ir leyendo el TAP poco a poco
            // y llegando a los bytes que indican TAMAÑO(2 bytes) + 0xFF(1 byte)

            //int numBlks = getNumBlocks(mFile, sizeTAP);
            
            if (!FILE_CORRUPTED)
            {
                // Reservo memoria para el descriptor de bloques del TAP
                _myTAP.descriptor = (tBlockDescriptor*)ps_calloc(MAX_BLOCKS_IN_TAP,sizeof(struct tBlockDescriptor));

                //  Inicializamos variables
                char nameTAP[11];
                char typeName[11];
                char blockName[11];

                int startBlock = 0;
                int lastStartBlock = 0;
                int sizeB = 0;
                int newSizeB = 0;
                int chk = 0;
                int blockChk = 0;
                int numBlocks = 0;
                int state = 0;    

                bool blockNameDetected = false;                
                bool reachEndByte = false;

                //Entonces recorremos el TAP. 
                SerialHW.println("");
                SerialHW.println("Analyzing TAP file. Please wait ...");
                
                // La primera cabecera SIEMPRE debe darse.
                // Los dos primeros bytes son el tamaño a contar
                sizeB = (256*sdm.readFileRange32(_mFile,startBlock+1,1,false)[0]) + sdm.readFileRange32(_mFile,startBlock,1,false)[0];
                startBlock = 2;

                while(reachEndByte==false && sizeB!=0)
                {
                    // Inicializamos
                    blockNameDetected = false;
                    
                    byte* tmpRng = allocateByte(sizeB);
                    tmpRng = sdm.readFileRange32(_mFile,startBlock,sizeB-1,false);
                    chk = calculateChecksum(tmpRng,0,sizeB-1);
                    
                    // Liberamos
                    delete [] tmpRng;
                    tmpRng = NULL;
                    
                    blockChk = sdm.readFileRange32(_mFile,startBlock+sizeB-1,1,false)[0];         

                    if (blockChk == chk)
                    {
                        
                        _myTAP.descriptor[numBlocks].offset = startBlock;
                        _myTAP.descriptor[numBlocks].size = sizeB;
                        _myTAP.descriptor[numBlocks].chk = chk;        

                        // Cogemos info del bloque
                        
                        // Flagbyte
                        // 0x00 - HEADER
                        // 0xFF - DATA BLOCK
                        int flagByte = sdm.readFileRange32(_mFile,startBlock,1,false)[0];

                        // 0x00 - PROGRAM
                        // 0x01 - ARRAY NUM
                        // 0x02 - ARRAY CHAR
                        // 0x03 - CODE FILE
                        int typeBlock = sdm.readFileRange32(_mFile,startBlock+1,1,false)[0];
                        
                        // Vemos si el bloque es una cabecera o un bloque de datos (bien BASIC o CM)
                        blockNameDetected = getInformationOfHead(_myTAP.descriptor[numBlocks],flagByte,typeBlock,startBlock,sizeB,nameTAP);

                        strncpy(_myTAP.descriptor[numBlocks].typeName,getTypeTAPBlock(_myTAP.descriptor[numBlocks].type),10)                       ;                      

                        if (blockNameDetected)
                        {                                     
                            _myTAP.descriptor[numBlocks].nameDetected = true;                                      
                        }
                        else
                        {
                            _myTAP.descriptor[numBlocks].nameDetected = false;
                        }

                        // Siguiente bloque
                        // Direcion de inicio (offset)
                        startBlock = startBlock + sizeB;
                        // Tamaño
                        newSizeB = (256*sdm.readFileRange32(_mFile,startBlock+1,1,false)[0]) + sdm.readFileRange32(_mFile,startBlock,1,false)[0];

                        numBlocks++;
                        sizeB = newSizeB;
                        startBlock = startBlock + 2;

                        _hmi.getMemFree();

                    }
                    else
                    {
                        reachEndByte = true;
                        SerialHW.println("Error in checksum. Block --> " + String(numBlocks) + " - offset: " + String(lastStartBlock));
                    }

                    // ¿Hemos llegado al ultimo byte
                    if (startBlock > sizeTAP)                
                    {
                        reachEndByte = true;
                        //break;
                        SerialHW.println("");
                        SerialHW.println("Success. End: ");
                    }

                }

                // Añadimos información importante
                strncpy(_myTAP.name,nameTAP,sizeof(nameTAP));
                _myTAP.size = sizeTAP;
                _myTAP.numBlocks = numBlocks;
            
            }
            else
            {
                // Añadimos información importante
                strncpy(_myTAP.name,"",1);
                _myTAP.size = 0;
                _myTAP.numBlocks = 0;            
            }

            _hmi.updateMem();
        }

        void showDescriptorTable()
        {
            SerialHW.println("");
            SerialHW.println("");
            SerialHW.println("++++++++++++++++++++++++++++++ Block Descriptor +++++++++++++++++++++++++++++++++++++++");

            int totalBlocks = _myTAP.numBlocks;

            for (int n=0;n<totalBlocks;n++)
            {
                SerialHW.print("[" + String(n) + "]" + " - Offset: " + String(_myTAP.descriptor[n].offset) + " - Size: " + String(_myTAP.descriptor[n].size));
                char* strType = &INITCHAR[0];
                
                switch(_myTAP.descriptor[n].type)
                {
                    case 0: 
                    strType = &STRTYPE0[0];
                    break;

                    case 1:
                    strType = &STRTYPE1[0];
                    break;

                    case 7:
                    strType = &STRTYPE7[0];
                    break;

                    case 2:
                    strType = &STRTYPE2[0];
                    break;

                    case 3:
                    strType = &STRTYPE3[0];
                    break;

                    case 4:
                    strType = &STRTYPE4[0];
                    break;

                    default:
                    strType=&STRTYPEDEF[0];
                }

                if (_myTAP.descriptor[n].nameDetected)
                {
                    SerialHW.println("");
                    //SerialHW.print("[" + String(n) + "]" + " - Name: " + (String(bDscr[n].name)).substring(0,10) + " - (" + strType + ")");
                    SerialHW.print("[" + String(n) + "]" + " - Name: " + _myTAP.descriptor[n].name + " - (" + strType + ")");
                }
                else
                { 
                    SerialHW.println("");
                    SerialHW.print("[" + String(n) + "] - " + strType + " ");
                }

                SerialHW.println("");
                SerialHW.println("");

            }      
        }

        int getTotalHeaders(byte* fileTAP, int sizeTAP)
        {
            // Este procedimiento devuelve el total de bloques que contiene el fichero
            int nblocks = 0;
            //byte* bBlock = new byte[sizeTAP];
            byte* bBlock;
            bBlock = allocateByte(sizeTAP);
            
            bBlock = fileTAP; 
            // Para ello buscamos la secuencia "0x13 0x00 0x00"
            for (int n=0;n<sizeTAP;n++)
            {
                if (bBlock[n] == 19)
                {
                    if ((n+1 < sizeTAP) && (bBlock[n+1] == 0))
                    {
                        if ((n+2 < sizeTAP) && (bBlock[n+2] == 0))
                        {
                            nblocks++;
                            n = n + 3;
                        }
                    }
                }
            }
            
            //free(bBlock);
            delete [] bBlock;
            bBlock = NULL;

            return nblocks;
        }

    public:
    
        void showInfoBlockInProgress(int nBlock)
        {
            switch(nBlock)
            {
                case 0:

                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("> PROGRAM HEADER");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE0[0],sizeof(&LASTYPE0[0]));
                    break;

                case 1:

                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> BYTE HEADER");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE1[0],sizeof(&LASTYPE1[0]));
                    break;

                case 7:

                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> SCREEN HEADER");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE7[0],sizeof(&LASTYPE7[0]));
                    break;

                case 2:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> BASIC PROGRAM");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE2[0],sizeof(&LASTYPE2[0]));
                    break;

                case 3:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> SCREEN");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE3[0],sizeof(&LASTYPE3[0]));
                    break;

                case 4:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> BYTE CODE");
                    #endif
                    if (LAST_SIZE != 6914)
                    {
                    strncpy(LAST_TYPE,&LASTYPE4_1[0],sizeof(&LASTYPE4_1[0]));
                    }
                    else
                    {
                    strncpy(LAST_TYPE,&LASTYPE4_2[0],sizeof(&LASTYPE4_2[0]));
                    }
                    break;

                case 5:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> ARRAY.NUM");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE5[0],sizeof(&LASTYPE5[0]));
                    break;

                case 6:
                    // Definimos el buffer del PLAYER igual al tamaño del bloque
                    #if LOG==3
                    SerialHW.println("");
                    SerialHW.println("> ARRAY.CHR");
                    #endif
                    strncpy(LAST_TYPE,&LASTYPE6[0],sizeof(&LASTYPE6[0]));
                    break;


            }        
        }

        byte* allocateByte(int size)
        {
            return((byte*)(ps_calloc(size,sizeof(byte))));
        }

        char* allocateChar(int size)
        {
            return((char*)(ps_calloc(size,sizeof(char))));
        }   

        void deallocatingTAP()
        {
            _hmi.getMemFree();
            _hmi.updateMem();

            log("Deallocating TAP");
            log("--------------------------------------");
            SerialHW.printf("Direccion de la copia %p", _myTAP.descriptor);
            
            //free(ptrDescriptorTAP);
            
            delete [] _myTAP.descriptor;
            _myTAP.descriptor = NULL;     

            _hmi.getMemFree();
            _hmi.updateMem();
        }
        
        void set_SdFat32(SdFat32 sdf32)
        {
            _sdf32 = sdf32;
        }

        void set_file(File32 tapFileName, int sizeTAP)
        {
            // Pasamos los parametros a la clase
            _mFile = tapFileName;
            _sizeTAP = sizeTAP;
        }

        void set_SDM(SDmanager sdmTmp)
        {
            //_sdm = sdmTmp;
            //ptrSdm = &sdmTmp;
        }

        void set_HMI(HMI hmi)
        {
            _hmi = hmi;
        }

        tTAP get_tap()
        {
            // Devolvemos el descriptor del TAP
            return _myTAP;
        }

        char* get_tap_name()
        {
            // Devolvemos el nombre del TAP
            return _myTAP.name;
        }

        int get_tap_numBlocks()
        {
            // Devolvemos el numero de bloques del TAP
            return _myTAP.numBlocks;
        }

        void initialize()
        {
            strncpy(_myTAP.name,"",1);
            _myTAP.numBlocks = 0;
            _myTAP.size = 0;
            CURRENT_BLOCK_IN_PROGRESS = 0;
            BLOCK_SELECTED = 0;
            _hmi.writeString("currentBlock.val=" + String(BLOCK_SELECTED));
            _hmi.writeString("progression.val=" + String(0));     
            //_hmi.getMemFree();
            _hmi.updateMem();
        }

        void terminate()
        {
            deallocatingTAP();

            strncpy(_myTAP.name,"",1);
            _myTAP.numBlocks = 0;
            _myTAP.size = 0;     
            
            _hmi.getMemFree();
            _hmi.updateMem();
        }

        bool proccess_tap(File32 tapFileName)
        {
            // Procesamos el fichero
            SerialHW.println("");
            SerialHW.println("Getting total blocks...");

            if (isFileTAP(tapFileName))
            {
                getBlockDescriptor(_mFile, _sizeTAP);
                if (!FILE_CORRUPTED)
                {
                    showDescriptorTable();
                }
                return true;
            }
            else
            {
                return false;
            }
        }

        void getInfoFileTAP(char* path) 
        {
        
            File32 tapFile;
            
            FILE_CORRUPTED = false;
            
            LAST_MESSAGE = "Analyzing file";
            _hmi.updateInformationMainPage();
            
            // Abrimos el fichero
            tapFile = sdm.openFile32(tapFile, path);
            
            // Obtenemos su tamaño total
            _mFile = tapFile;
            _rlen = tapFile.available();
            
            // creamos un objeto TAPproccesor
            set_file(tapFile, _rlen);
            
            // Actualizamos el indicador de memoria
            _hmi.getMemFree();
            _hmi.updateMem();

            if (proccess_tap(tapFile))
            {
                SerialHW.println("");
                SerialHW.println("");
                SerialHW.println("END PROCCESING TAP: ");

                if (_myTAP.descriptor != NULL)
                {
                    // Entregamos información por consola
                    PROGRAM_NAME = _myTAP.name;
                    TOTAL_BLOCKS = _myTAP.numBlocks;
                    strncpy(LAST_TYPE,&INITCHAR2[0],sizeof(&INITCHAR2[0]));
                
                    SerialHW.println("");
                    SerialHW.println("");
                    SerialHW.println("PROGRAM_NAME: " + PROGRAM_NAME);
                    SerialHW.println("TOTAL_BLOCKS: " + String(TOTAL_BLOCKS));
                
                    // Pasamos informacion del descriptor al HMI         
                    _hmi.setBasicFileInformation(_myTAP.descriptor[BLOCK_SELECTED].name,_myTAP.descriptor[BLOCK_SELECTED].typeName,_myTAP.descriptor[BLOCK_SELECTED].size);
                    // Actualizamos la pantalla
                    _hmi.updateInformationMainPage();
                }          
            }
            else
            {
                FILE_CORRUPTED = true;
            }
        }

        void play() 
        {

            if (_myTAP.descriptor != NULL)
            {         
            
                    // Inicializamos el buffer de reproducción. Memoria dinamica
                    byte* bufferPlay;

                    // Entregamos información por consola
                    PROGRAM_NAME = _myTAP.name;
                    TOTAL_BLOCKS = _myTAP.numBlocks;
                    strncpy(LAST_NAME,&INITCHAR2[0],sizeof(&INITCHAR2[0]));

                    // Ahora reproducimos todos los bloques desde el seleccionado (para cuando se quiera uno concreto)
                    int m = BLOCK_SELECTED;
                    //BYTES_TOBE_LOAD = _rlen;

                    // Reiniciamos
                    if (BLOCK_SELECTED == 0) 
                    {
                    BYTES_LOADED = 0;
                    BYTES_TOBE_LOAD = _rlen;
                    //_hmi.writeString("");
                    _hmi.writeString("progressTotal.val=" + String((int)((BYTES_LOADED * 100) / (BYTES_TOBE_LOAD))));
                    } 
                    else 
                    {
                    BYTES_TOBE_LOAD = _rlen - _myTAP.descriptor[BLOCK_SELECTED - 1].offset;
                    }

                    for (int i = m; i < _myTAP.numBlocks; i++) 
                    {

                    // Obtenemos el nombre del bloque
                    strncpy(LAST_NAME,_myTAP.descriptor[i].name,sizeof(_myTAP.descriptor[i].name));
                    LAST_SIZE = _myTAP.descriptor[i].size;

                    // Almacenmas el bloque en curso para un posible PAUSE
                    if (LOADING_STATE != 2) 
                    {
                        CURRENT_BLOCK_IN_PROGRESS = i;
                        BLOCK_SELECTED = i;

                        _hmi.writeString("currentBlock.val=" + String(i + 1));
                        _hmi.writeString("progression.val=" + String(0));
                    }

                    //Paramos la reproducción.
                    if (LOADING_STATE == 2) 
                    {
                        PAUSE = false;
                        STOP = true;
                        PLAY = false;

                        i = _myTAP.numBlocks+1;

                        SerialHW.println("");
                        SerialHW.println("LOADING_STATE 2");

                        return;
                    }

                    //Ahora vamos lanzando bloques dependiendo de su tipo
                    //Esto actualiza el LAST_TYPE
                    showInfoBlockInProgress(_myTAP.descriptor[i].type);

                    // Actualizamos HMI
                    _hmi.setBasicFileInformation(_myTAP.descriptor[BLOCK_SELECTED].name,_myTAP.descriptor[BLOCK_SELECTED].typeName,_myTAP.descriptor[BLOCK_SELECTED].size);

                    _hmi.updateInformationMainPage();

                    // Reproducimos el fichero
                    if (_myTAP.descriptor[i].type == 0) 
                    {

                        // Reservamos memoria para el buffer de reproducción
                        bufferPlay = allocateByte(_myTAP.descriptor[i].size);
                        bufferPlay = sdm.readFileRange32(_mFile, _myTAP.descriptor[i].offset, _myTAP.descriptor[i].size, false);

                        // *** Cabecera PROGRAM
                        // Llamamos a la clase de reproducción
                        zxp.playData(bufferPlay, _myTAP.descriptor[i].size,DPILOT_HEADER * DPULSE_PILOT);

                        // Liberamos el buffer de reproducción
                        delete [] bufferPlay;
                        bufferPlay = NULL;
                    } 
                    else if (_myTAP.descriptor[i].type == 1 || _myTAP.descriptor[i].type == 7) 
                    {
                        
                        bufferPlay = allocateByte(_myTAP.descriptor[i].size);
                        bufferPlay = sdm.readFileRange32(_mFile, _myTAP.descriptor[i].offset, _myTAP.descriptor[i].size, false);

                        // *** Cabecera BYTE
                        // Llamamos a la clase de reproducción
                        zxp.playData(bufferPlay, _myTAP.descriptor[i].size,DPILOT_HEADER * DPULSE_PILOT);

                        // Liberamos el buffer de reproducción
                        delete [] bufferPlay;
                        bufferPlay = NULL;
                    } 
                    else 
                    {
                        // *** Bloque de DATA
                        int blockSize = _myTAP.descriptor[i].size;

                        // Si el SPLIT esta activado y el bloque es mayor de 20KB hacemos Split.
                        if ((SPLIT_ENABLED) && (blockSize > SIZE_TO_ACTIVATE_SPLIT)) 
                        {

                            // Lanzamos dos bloques
                            int bl1 = blockSize / 2;
                            int bl2 = blockSize - bl1;
                            int blockPlaySize = 0;
                            int offsetPlay = 0;

                            for (int j = 0; j < 2; j++) 
                            {

                                if (j == 0) 
                                {
                                    
                                    // Cortamos la primera mitad del bloque
                                    blockPlaySize = bl1;
                                    bufferPlay = allocateByte(blockPlaySize);
                                    offsetPlay = _myTAP.descriptor[i].offset;
                                    bufferPlay = sdm.readFileRange32(_mFile, offsetPlay, blockPlaySize, true);
                                    
                                    // Reproducimos la primera mitad
                                    zxp.playDataBegin(bufferPlay, blockPlaySize,DPILOT_DATA * DPULSE_PILOT);
                                    
                                    // Liberamos el buffer de reproducción
                                    delete [] bufferPlay;
                                    bufferPlay = NULL;                            
                                } 
                                else 
                                {
                                    // Cortamos el final del bloque
                                    blockPlaySize = bl2;
                                    offsetPlay = offsetPlay + bl1;
                                    bufferPlay = allocateByte(blockPlaySize);
                                    bufferPlay = sdm.readFileRange32(_mFile, offsetPlay, blockPlaySize, true);

                                    // Reproducimos la ultima mitad
                                    zxp.playDataEnd(bufferPlay, blockPlaySize,DPILOT_DATA * DPULSE_PILOT);

                                    // Liberamos el buffer de reproducción
                                    delete [] bufferPlay;
                                    bufferPlay = NULL;
                                }
                            }
                        } 
                        else 
                        {
                            // En el caso de NO USAR SPLIT o el bloque es menor de 20K
                            bufferPlay = allocateByte(_myTAP.descriptor[i].size);
                            bufferPlay = sdm.readFileRange32(_mFile, _myTAP.descriptor[i].offset, _myTAP.descriptor[i].size, false);
                            
                            // Reproducimos el bloque de datos
                            zxp.playData(bufferPlay, _myTAP.descriptor[i].size,DPILOT_DATA * DPULSE_PILOT);

                            // Liberamos el buffer de reproducción
                            delete [] bufferPlay;
                            bufferPlay=NULL;
                        }
                    }
                    }

                    SerialHW.println("");
                    SerialHW.println("Playing was finish.");

                    // En el caso de no haber parado manualmente, 
                    // Lanzamos el AUTO-STOP
                    if (LOADING_STATE == 1) 
                    {
                        PLAY = false;
                        STOP = true;
                        PAUSE = false;

                        LAST_MESSAGE = "Playing end. Automatic STOP.";

                        _hmi.setBasicFileInformation(_myTAP.descriptor[BLOCK_SELECTED].name,_myTAP.descriptor[BLOCK_SELECTED].typeName,_myTAP.descriptor[BLOCK_SELECTED].size);
                        _hmi.updateInformationMainPage();

                        SerialHW.println("");
                        SerialHW.println("LOADING_STATE 1");
                    }              
            }
            else
            {
                // No se ha seleccionado ningún fichero
                LAST_MESSAGE = "No file selected.";
                _hmi.setBasicFileInformation(_myTAP.descriptor[BLOCK_SELECTED].name,_myTAP.descriptor[BLOCK_SELECTED].typeName,_myTAP.descriptor[BLOCK_SELECTED].size);
                _hmi.updateInformationMainPage();
            }

        }

        // Constructor de la clase
        TAPproccesor(AudioKit kit)
        {}      

};
