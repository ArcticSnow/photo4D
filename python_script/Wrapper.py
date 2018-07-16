# coding : utf8
from tkinter import *
import tkinter.filedialog
from tkinter.ttk import Progressbar

def process_graph():

    fenetre = Tk()
    fenetre.geometry("750x500")

    label = Label(fenetre, text="Lancement de la reconstruction 3D pour les fichiers Time-laps")
    label.pack()

    bouton = Button(fenetre, text="Avancé")
    bouton.pack()


    options2 = LabelFrame(fenetre,text="Options MicMac", borderwidth=2, relief=GROOVE)
    options2.pack( padx=10, pady=10,fill="both", expand="yes")

    Label(options2, text="Mode de reconstruction",borderwidth=3).grid(row=2,column=1)
    reconstruction_mode = StringVar(options2)
    reconstruction_mode.set("MicMac")
    liste = OptionMenu(options2, reconstruction_mode, "QuickMac", "MicMac", "BigMac")
    liste.grid(row=2,column=2,sticky=W)

    Label(options2, text="Pourcentage de sous echantillonage",borderwidth=3).grid(row=1, column=1)
    value = DoubleVar()
    scale = Scale(options2, variable=value,orient=HORIZONTAL)
    value.set(50)
    scale.grid(row=1,column=2,sticky=W)


    def check_buttons():
        if use_ori.get() == 1:
            case2['state'] = DISABLED
            cal_folder['state']=DISABLED
            button3['state']=DISABLED
        else:
            case2['state'] = NORMAL
            cal_folder['state'] = NORMAL
            button3['state'] = NORMAL
    use_ori = IntVar()
    case = Checkbutton(options2, text="Utiliser une orientation initiale", variable=use_ori,command=check_buttons)
    case.grid(row=3,column=1)
    ori = StringVar()
    ori.set("")
    ori_folder = Label(options2, textvariable=ori)
    ori_folder.grid(row=4, column = 2,sticky=W)

    def ask_ori_folder():
        directory = tkinter.filedialog.askdirectory()
        ori.set(directory)

    button2 = Button(options2, text="dossier",cursor="pirate", command=ask_ori_folder)
    button2.grid(row=4,column=1)

    calc_ori = IntVar()
    case_calc_ori = Checkbutton(options2, text="Réestimer l'orientation", variable=calc_ori)
    case_calc_ori.grid(row=4,column=3)


    button2['command']=check_buttons
    use_cal = IntVar()
    case2 = Checkbutton(options2, text="Utiliser une calibration initiale", variable=use_cal, command=check_buttons)
    case2.grid(row=5, column=1)
    cal = StringVar()
    cal.set("")
    cal_folder = Label(options2, textvariable=cal)
    cal_folder.grid(row=6, column=2, sticky=W)

    def ask_cal_folder():
        directory = tkinter.filedialog.askdirectory()
        cal.set(directory)

    button3 = Button(options2, text="dossier", cursor="dotbox", command=ask_cal_folder)
    button3.grid(row=6, column=1)

    def check_gcp():
        if use_gcp.get():
            for child in frame_gcp.winfo_children():
                child.configure(state='normal')
        else:
            for child in frame_gcp.winfo_children():
                child.configure(state='disable')

    use_gcp = IntVar()
    case_gcp = Checkbutton(options2, text="Utiliser des points d'appuis", variable=use_gcp, command=check_gcp)
    case_gcp.grid(row=7, column=1)
    frame_gcp=LabelFrame(options2, text="Points d'Appuis",borderwidth=2, relief=GROOVE)
    frame_gcp.grid(row=8,column=1,columnspan=3)
    Label(frame_gcp,text="Fichier de coordonnées MicMac  :").grid(row=1,column=1)
    coord_file = StringVar()
    coord_file.set("coordinates.xml")
    Label(frame_gcp, textvariable=coord_file).grid(row=1,column=3)

    def ask_coord_file():
        directory = tkinter.filedialog.askopenfilename(filetypes = (("Xml files","*.xml"),("all files","*.*")))
        coord_file.set(directory)
    Button(frame_gcp, width=4, cursor="clock", command=ask_coord_file).grid(row=1,column=2)
    Label(frame_gcp, text="Fichier de mesures images  :").grid(row=2, column=1)
    measures_file = StringVar()
    measures_file.set("Measures-S2D.xml")
    Label(frame_gcp, textvariable=measures_file).grid(row=2, column=3)

    def ask_measures_file():
        directory = tkinter.filedialog.askopenfilename(filetypes=(("Xml files", "*.xml"), ("all files", "*.*")))
        measures_file.set(directory)

    Button(frame_gcp, width=4, command=ask_measures_file).grid(row=2, column=2)




    def launch():
        window_process = Tk()
        bar = Progressbar(window_process, length=200)
        bar['value'] = 30
        bar.pack()
        abrupt = Button(window_process, text="Fermer", command=fenetre.quit)
        abrupt.pack()

    launch = Button(fenetre,text="Lancer la reconstruction",command=launch)
    launch.pack()


    check_buttons()
    check_gcp()
    fenetre.mainloop()
if __name__ == "__main__":
    process_graph()