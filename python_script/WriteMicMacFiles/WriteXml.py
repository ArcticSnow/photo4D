# coding :utf8

from lxml import etree

def write_S3D_xmlfile(list_pt_measures, file_name):
    """
    Write  an xml file with 3D coordinates of points, in a way that MicMac can read it
    :param list_pt_measures: list containing 3D measures in the shape :
    [[NamePt (String), coordinates (String, like 'coord1 coord2 coord3'), incertitude (String, like 'Icoord1, Icoor2, Icoord3', optional'], ...]
    :param file_name: path or name of the output file
    """
    # Creation of the document root
    measures_set = etree.Element('DicoAppuisFlottant')
    for pt in list_pt_measures:
        pt_coord = etree.SubElement(measures_set, 'OneAppuisDAF')
        # coordinates of the point
        coord_pt = etree.SubElement(pt_coord, 'Pt')
        coord_pt.text = str(pt[1])
        # name of the point
        name_pt = etree.SubElement(pt_coord, 'NamePt')
        name_pt.text = str(pt[0])
        # incertitude of the coordinates
        coord_img_pt = etree.SubElement(pt_coord, 'Incertitude')
        try:
            coord_img_pt.text = str(pt[2])
        except IndexError:
            coord_img_pt.text = "1 1 1"

        try:
            # We open the file for writing
            with open(file_name, 'w') as file:
                # Header
                file.write('<?xml version="1.0" encoding="UTF_8"?>\n')
                # Writing all the text we created
                file.write(etree.tostring(measures_set, pretty_print=True).decode('utf-8'))
        except IOError:
            print('Error while writing file')
            exit(1)


def write_S2D_xmlfile(list_img_measures, file_name):
    """
    Write  an xml file with 2D mesures of points in different images, in a way that MicMac can read it
    :param list_img_measures: list containing 2D measures. Must looks like :
    [[NameImage1 (String), [NamePoint1 (String), measure (String, 'coordPoint1Image1 coordPoint1Image1')],
                           [NamePoint2 (String), measure (String, 'coordPoint2Image1 coordPoint2Image1')],
                           ...],
     [NameImage2 (String), [NamePoint1 (String), measure (String, 'coordPoint1Image2 coordPoint1Image2')],
                           [NamePoint2 (String), measure (String, 'coordPoint2Image1 coordPoint2Image2')],
                           ...], ...]
    :param file_name: path or name of the output file
    """
    # Creation of the document root
    measures_set = etree.Element('SetOfMesureAppuisFlottants')
    for img in list_img_measures:
        img_meas = etree.SubElement(measures_set, 'MesureAppuiFlottant1Im')
        name_img = etree.SubElement(img_meas, 'NameIm')
        name_img.text = str(img[0])
        for measure in img[1]:
            pt_mes = etree.SubElement(img_meas, 'OneMesureAF1I')
            name_pt = etree.SubElement(pt_mes, 'NamePt')
            name_pt.text = str(measure[0])
            coord_img_pt = etree.SubElement(pt_mes, 'PtIm')
            coord_img_pt.text = str(measure[1])

    try:
        # We open the file for writing
        with open(file_name, 'w') as file:
            # Header
            file.write('<?xml version="1.0" encoding="UTF_8"?>\n')
            # Writing all the text we created
            file.write(etree.tostring(measures_set, pretty_print=True).decode('utf-8'))
    except IOError:
        print('Error while writing file')
        exit(1)


if __name__ == "__main__":
    liste_mesures = [['DSC00047.JPG', [['1', '5155.32345161082321 1709.62885559043229']]],
                     ['DSC00048.JPG', [['1', '5223.24245336298645 1654.30485908846413']]],
                     ['DSC00049.JPG', [['1', '5225.28907384436934 1935.98648985141676']]],
                     ['DSC00050.JPG', []]]

    write_S2D_xmlfile(liste_mesures, 'Appuis_fictifs-S2D.xml')

    liste_points3D = [['1', "-23.4605861800590318 1.71111440194407338 26.4778679705422384", "1 1 1"],
                      ['1', "15.9331147514487199 -5.33682558320814415 102.277413480224084"]]

    write_S3D_xmlfile(liste_points3D, 'Appuis_fictifs-S3D.xml')
