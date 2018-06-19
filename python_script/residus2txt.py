# -*- coding: utf-8 -*-
"""
Script permettant d'afficher les resultats de la derniere iteration contenus 
dans le fichier residus.xml
Pour fonctionner il a besoin d'etre place dans le dossier Ori correespondant 
Cree un fichier .txt dans le dossier Ori, mais sous forme de texte delimite par
des ';' et donc convertissable en csv
"""

from lxml import etree

if __name__ == "__main__":
    
    xmlfile = 'Residus.xml'
    elements = ('Name', 'Residual', 'PercOk', 'NbPts', 'NbPtsMul')
    
    #Creation du fichier
    file = open("result_last_iter.txt", "w")
    
    #Parcours du fichier residus.xml
    tree = etree.parse(xmlfile)
    
    #Recuperation du nombre total d'etapes
    nb_iters=tree.xpath("/XmlSauvExportAperoGlob/Iters/NumIter")[-1].text
    file.write('nb_iters;' + nb_iters + '\n')
    
    #Recuperation de la moyenne des residus de la derniere iteration
    av_resid = tree.xpath("/XmlSauvExportAperoGlob/Iters[NumIter={}][NumEtape=3]/\
                            AverageResidual".format(nb_iters))[0].text
    file.write('AverageResidual;' + av_resid +'\n')
    
    
    #Recuperation des donnees pour chaque image de la derniere iteration
    file.write('\nName;Residual;PercOk;NbPts;NbPtsMul\n')
    for img in tree.xpath("/XmlSauvExportAperoGlob/Iters[NumIter={}]\
                                                         [NumEtape=3]/OneIm".format(nb_iters)):
        obj = ''
        for e in elements:
            obj += img.find(e).text+';'
        file.write(obj+'\n')
    
    file.close()
    main()