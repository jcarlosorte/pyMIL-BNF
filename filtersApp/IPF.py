# -*- coding: utf-8 -*-
"""
Created on Sun May 12 00:18:24 2019

@author: Juan Carlos
"""

#imports
import warnings,copy
from MILpy.data.load_data import load_data
import random as rand
import numpy as np
import pandas as pd
from sklearn.utils import shuffle
from sklearn.model_selection import StratifiedKFold
warnings.filterwarnings('ignore')
from sklearn.metrics import roc_auc_score, accuracy_score
#from funciones import fun_aux
#Import Algorithms 
from MILpy.Algorithms.simpleMIL import simpleMIL
from MILpy.Algorithms.MILBoost import MILBoost
from MILpy.Algorithms.maxDD import maxDD
from MILpy.Algorithms.CKNN import CKNN
from MILpy.Algorithms.EMDD import EMDD
#from MILpy.Algorithms.MILES import MILES
from MILpy.Algorithms.BOW import BOW

def IPF(b,votacion,folds,ruido,clasif_O,clasif_F):
    for DataSet in b:
        bags,labels,X = load_data(DataSet)
        bags,labels = shuffle(bags, labels, random_state=rand.randint(0, len(labels)-1))
        skf = StratifiedKFold(n_splits=folds)
        print('\n\tDATASET: '+str(DataSet)+'\n')
        
        for ny,k in enumerate(ruido):
            print('\t\t=>RUIDO : '+str(k))
            file_data = '../filtersApp/tabla.csv'
            data = {}
            data['IPF'] = []
            data['Original'] = []
            
            Clasificadores_fake = clasif()
            Clasificadores = []
            for s,cl in enumerate(Clasificadores_fake):
                if str(cl[2]) == clasif_O:
                    Clasificadores.append(cl)
            
            Clasificadores_fake2 = cla_filter_ipf()
            Clasificadores_filtro = []
            for s,cl in enumerate(Clasificadores_fake2):
                if str(cl[2]) == clasif_F:
                    Clasificadores_filtro.append(cl)
            for h,cl_f0 in enumerate(Clasificadores_filtro):
                    data[str(cl_f0[2])] = []
            
            for s,cl in enumerate(Clasificadores):
                fold = 1
                results_Fil = [[] for x in range(len(Clasificadores_filtro))] 
                results_Ori = []
                clasificador_ = Clasificadores[s]
                for train_index, test_index in skf.split(bags, labels.reshape(len(labels))):
#                    print('\t\t\t=>FOLD : '+str(fold))
                    X_train = [bags[i] for i in train_index]        
                    Y_train = labels[train_index]
                    X_test  = [bags[i] for i in test_index]
                    Y_test  = labels[test_index]
                    LabelToChange = Porcentaje(len(train_index),k)
                    aleatorios = rand.sample(range(0,len(train_index)),int(LabelToChange))
                    for al in aleatorios:
                        if Y_train[al] == 0:
                            Y_train[al] = Y_train[al]+1
                        else:
                            Y_train[al] = Y_train[al]-1

                    for j,cl_f in enumerate(Clasificadores_filtro):
                        clasificador_f = Clasificadores_filtro[j]
#                        print('\t\t\t=>Filtrado con '+str(cl_f[2]))
                        X_train_NoNy,Y_train_NoNy = mil_cv_filter_ipf(X_train,Y_train,folds,votacion,clasificador_f) 
                        results_Fil[j].append(filtrado_final(X_train_NoNy,Y_train_NoNy,X_test,Y_test,clasificador_))

#                    print('\t\t\t=>Original')
                    results_Ori.append(filtrado_final(X_train,Y_train,X_test,Y_test,clasificador_))
                    fold = fold + 1
                results_accuracie_O = []
                results_auc_O = []
                print('\t\t\t\t-->Clasificador :'+str(clasificador_[2]))
                data['IPF'].append(str(clasificador_[2]))
                for g in range(0,folds):
                    results_accuracie_O.append(results_Ori[g][0])
                    results_auc_O.append(results_Ori[g][1])
                print('\t\t\t\t\t-->Original')
                print('\t\t\t\t\t Precision: '+ str(np.mean(results_accuracie_O, dtype=np.float64))+'%')
                data['Original'].append(np.mean(results_accuracie_O))
                print('\t\t\t\t\t Roc Score: '+ str(np.mean(results_auc_O, dtype=np.float64)))
                
                for h,cl_f0 in enumerate(Clasificadores_filtro):
                    results_accuracie_F = []
                    results_auc_F = []
                    print('\t\t\t\t\t-->Filtrado por '+str(cl_f0[2]))
                    for f in range(0,folds):
                        results_accuracie_F.append(results_Fil[h][f][0])
                        results_auc_F.append(results_Fil[h][f][1])  
                    print('\t\t\t\t\t Precision: '+ str(np.mean(results_accuracie_F, dtype=np.float64))+'%')
                    data[str(cl_f0[2])].append(np.mean(results_accuracie_F))
                    print('\t\t\t\t\t Roc Score: '+ str(np.mean(results_auc_F, dtype=np.float64)))
            df = pd.DataFrame(data)
            df.to_csv(file_data, sep=';')
    
def mil_cv_filter_ipf(bags_f,labels_f,folds,votacion,clasificador_):
#    print('\t\t\tFiltrando...')
    error = 0.01
    toStop = 3
    stop = True
    countToStop = 0
    if len(labels_f) < folds:
        folds = len(labels_f)
    skf = StratifiedKFold(n_splits=folds)
    totalNoisyLabel = 0
    while stop:
        bags_f,labels_f = shuffle(bags_f, labels_f, random_state=rand.randint(0, len(labels_f)-1))
        isCorrectLabel = np.ones((folds, len(labels_f)), dtype=bool)
        fold = 0        
        for train_index, test_index in skf.split(bags_f, labels_f.reshape(len(labels_f))):
            X_train = [bags_f[i] for i in train_index]        
            Y_train = labels_f[train_index]
#            print('\t\t\t=>FOLD : '+str(fold))
            try:
                if len(clasificador_[1]) > 0:
                    clasificador_[0].fit(X_train, Y_train, **clasificador_[1])
                else:
                    clasificador_[0].fit(bags_f, labels_f)
                predictions = clasificador_[0].predict(X_train)
                if (isinstance(predictions, tuple)):
                    predictions = predictions[0]
            except:
                print('Fallo, segundo intento')
                try:
                    if len(clasificador_[1]) > 0:
                        clasificador_[0].fit(X_train, Y_train, **clasificador_[1])
                    else:
                        clasificador_[0].fit(bags_f, labels_f)
                    predictions = clasificador_[0].predict(X_train)
                    
                    if (isinstance(predictions, tuple)):
                        predictions = predictions[0]
                    print('OK')
                except:
                    print('Posible fallo en bolsa...')
                    try:
                        print('Cambiando clasificador..')
                        Cla_error = simpleMIL()
                        par_error = {'type': 'max'}
                        if len(par_error) > 0:
                            Cla_error.fit(X_train, Y_train, **par_error)
                        else:
                            Cla_error.fit(X_train, Y_train)
                        predictions = Cla_error.predict(X_train)
                        if (isinstance(predictions, tuple)):
                            predictions = predictions[0]
                        print('OK')
                    except:
                        predictions = np.ones((1, len(Y_train)), dtype=int)
                        predictions = predictions[0]
                        print('Fallo')
            for l,p in enumerate(train_index):
                try:
                    isCorrectLabel[fold][p] = (Y_train.T[0][l] == np.sign(predictions[l]))
                except IndexError:
                    print("Fallo en ultimo indice!")
            fold = fold + 1
        if votacion == 'maxVotos':
            noisyBags = []
            for n in range(0,len(labels_f)):
                aux = 0
                for m in range(0,folds):
                    if not isCorrectLabel[m][n]:
                        aux = aux+1
                if aux > folds/2:
                    noisyBags.append(n)
        if votacion == 'consenso':
            noisyBags = []
            for n in range(0,len(labels_f)):
                aux = True
                for m in range(0,folds):
                    if aux:
                        if isCorrectLabel[m][n]:
                            aux = False
                if aux:
                    noisyBags.append(n)
        nonNoisyBags = [] 
        cont = 0
        if len(noisyBags) == 0:
            for z in range(0,len(bags_f)):
                nonNoisyBags.append(z)
        else:
            for z in range(0,len(bags_f)):
                if cont < len(noisyBags) and noisyBags[cont] == z:
                    cont = cont + 1
                else:
                    nonNoisyBags.append(z)
        if len(noisyBags) < (len(bags_f)*error):
            countToStop = countToStop + 1
        else:
            countToStop = 0
        if countToStop == toStop:
            stop = False
        else:
            bags_f = [bags_f[d] for d in nonNoisyBags] 
            labels_f = labels_f[nonNoisyBags]
        if len(bags_f) < len(labels_f.reshape(len(labels_f))):
            print('Número de bolsas, menor al número de etiquetas, no se puede continuar')
            stop = False
        #Comprobacion nueva 28/10/19
        if len(labels_f) < 1:
            stop = False
        totalNoisyLabel+=len(noisyBags)
    print('\t\t\t=>Elementos eliminados por '+clasificador_[2]+': '+str(totalNoisyLabel))
    X_train_NoNy = bags_f
    Y_train_NoNy = labels_f
    return X_train_NoNy,Y_train_NoNy

def filtrado_final(X_train,Y_train,X_test,Y_test,clasificador_):  
    results = np.zeros((2))
    accuracie = 0
    auc_score = 0
    aux_lab = True
    if len(np.unique(Y_train)) == 1:
        if Y_train[0] == 0:
            for b in range(0,len(Y_test)):
                if aux_lab:
                    if Y_test[b] == 1:
                        aux_Y_train = copy.copy(Y_test[b])
                        aux_X_train = copy.copy(X_test[b])
                        Y_test[b] = copy.copy(Y_train[0])
                        X_test[b] = copy.copy(X_train[0])
                        Y_train[0] = copy.copy(aux_Y_train)
                        X_train[0] = copy.copy(aux_X_train)
                        aux_lab = False
        else:
            for b in range(0,len(Y_test)):
                if aux_lab:
                    if Y_test[b] == 0:
                        aux_Y_train = copy.copy(Y_test[b])
                        aux_X_train = copy.copy(X_test[b])
                        Y_test[b] = copy.copy(Y_train[0])
                        X_test[b] = copy.copy(X_train[0])
                        Y_train[0] = copy.copy(aux_Y_train)
                        X_train[0] = copy.copy(aux_X_train)
                        aux_lab = False
    try:
        if len(clasificador_[1]) > 0:
            clasificador_[0].fit(X_train, Y_train, **clasificador_[1])
        else:
            clasificador_[0].fit(X_train, Y_train)
        predictions = clasificador_[0].predict(X_test) 
        if (isinstance(predictions, tuple)):
            predictions = predictions[0]
        accuracie = (100 * np.average(Y_test.T == np.sign(predictions)))
        auc_score = (100 * roc_auc_score_FIXED(Y_test,predictions))
    except:
        print('Fallo, segundo intento')
      
        try:
            if len(clasificador_[1]) > 0:
                clasificador_[0].fit(X_train, Y_train, **clasificador_[1])
            else:
                clasificador_[0].fit(X_train, Y_train)
            predictions = clasificador_[0].predict(X_test) 
            if (isinstance(predictions, tuple)):
                predictions = predictions[0]
            accuracie = (100 * np.average(Y_test.T == np.sign(predictions)))   
            auc_score = (100 * roc_auc_score_FIXED(Y_test,predictions))
            print('OK')     
        except:
            accuracie = 0.0
            auc_score = 0.0
            print('Fallo en calculo') 
    results[0] = accuracie
    results[1] = auc_score
#    print('\t\t\t\t\t Precisión: '+ str(accuracie)+'%\n\t\t\t\t\t Roc Score: '+ str(auc_score))
    return results

def roc_auc_score_FIXED(y_true, y_pred):
    if len(np.unique(y_true)) == 1 or len(np.unique(y_true)) == 0: # bug in roc_auc_score
        return accuracy_score(y_true, np.rint(y_pred))
    return roc_auc_score(y_true, y_pred)

def Porcentaje(X,Y):
    return X*Y/100

def clasif():
    aux = []
    resul1 = [[],[],[],[],[],[],[]]
    roc_m_1 = [[],[],[],[],[],[],[]]
    SMILaMax = [simpleMIL(),{'type': 'max'},'MIL max',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    SMILaMin = [simpleMIL(),{'type': 'min'},'MIL min',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    SMILaExt = [simpleMIL(),{'type': 'extreme'},'MIL Extreme',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    BOW_clas = [BOW(),{'k':90,'covar_type':'diag','n_iter':20},'BOW',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    CKNN_cla = [CKNN(),{'references': 3, 'citers': 5},'CKNN',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    maxDD_cl = [maxDD(),{},'DIVERSE DENSITY',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    EMDD_cla = [EMDD(),{},'EM-DD',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    MILB_cla = [MILBoost(),{},'MILBOOST',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
#    MILES_cl = [MILES(),{},'MILES',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    aux.append(SMILaMax)
    aux.append(SMILaMin)
    aux.append(SMILaExt)
    aux.append(BOW_clas)
    aux.append(CKNN_cla)
    aux.append(maxDD_cl)
    aux.append(EMDD_cla)
    aux.append(MILB_cla)
#    aux.append(MILES_cl)
    return aux

def cla_filter_ipf():
    aux = []
    resul1 = [[],[],[],[],[],[],[]]
    roc_m_1 = [[],[],[],[],[],[],[]]
    SMILaMax = [simpleMIL(),{'type': 'max'},'MIL max',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    SMILaMin = [simpleMIL(),{'type': 'min'},'MIL min',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    SMILaExt = [simpleMIL(),{'type': 'extreme'},'MIL Extreme',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    BOW_clas = [BOW(),{'k':90,'covar_type':'diag','n_iter':20},'BOW',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    CKNN_cla = [CKNN(),{'references': 3, 'citers': 5},'CKNN',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    maxDD_cl = [maxDD(),{},'DIVERSE DENSITY',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    EMDD_cla = [EMDD(),{},'EM-DD',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    MILB_cla = [MILBoost(),{},'MILBOOST',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
#    MILES_cl = [MILES(),{},'MILES',copy.deepcopy(resul1),copy.deepcopy(roc_m_1)]
    aux.append(SMILaMax)
    aux.append(SMILaMin)
    aux.append(SMILaExt)
    aux.append(BOW_clas)
    aux.append(CKNN_cla)
    aux.append(maxDD_cl)
    aux.append(EMDD_cla)
    aux.append(MILB_cla)
#    aux.append(MILES_cl)
    return aux