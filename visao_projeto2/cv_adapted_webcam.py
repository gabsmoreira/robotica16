# -*- coding:utf-8 -*-

from pylab import *
from numpy import *
from PIL import Image
from matplotlib import pyplot as plt

import cv2

### Extracted from Programming Computer Vision With Python, by Jan Solem
### http://programmingcomputervision.com/
### Adapted to use OpenCV and avoid VLFEAT


# If you have PCV installed, these imports should work
import homography, camera, sift



# Stuff for sift
FLANN_INDEX_KDTREE = 0
index_params = dict(algorithm = FLANN_INDEX_KDTREE, trees = 5)
search_params = dict(checks = 50)
flann = cv2.FlannBasedMatcher(index_params, search_params)
MIN_MATCH_COUNT = 10


def find_homography(kp1, des1, kp2, des2):
    """
        Given a set of keypoints and descriptors finds the homography
    """
    # Tenta fazer a melhor comparacao usando o algoritmo
    matches = flann.knnMatch(des1, des2, k=2)

    # store all the good matches as per Lowe's ratio test.
    good = []
    for m,n in matches:
        if m.distance < 0.7*n.distance:
            good.append(m)

    if len(good)>MIN_MATCH_COUNT:
        # Separa os bons matches na origem e no destino
        src_pts = np.float32([ kp1[m.queryIdx].pt for m in good ]).reshape(-1,1,2)
        dst_pts = np.float32([ kp2[m.trainIdx].pt for m in good ]).reshape(-1,1,2)


        # Tenta achar uma trasformacao composta de rotacao, translacao e escala que situe uma imagem na outra
        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC,5.0)
        matchesMask = mask.ravel().tolist()

        h,w = img1.shape
        pts = np.float32([ [0,0],[0,h-1],[w-1,h-1],[w-1,0] ]).reshape(-1,1,2)

        # Transforma os pontos da imagem origem para onde estao na imagem destino
        dst = cv2.perspectiveTransform(pts,M)

        return M
    else:
        # Caso em que nao houve matches o suficiente
        return -1



"""
This is the augmented reality and pose estimation cube example from Section 4.3.
"""

def cube_points(c,wid):
    """ Creates a list of points for plotting
        a cube with plot. (the first 5 points are
        the bottom square, some sides repeated). """
    p = []
    # bottom
    p.append([c[0]-wid,c[1]-wid,c[2]-wid])
    p.append([c[0]-wid,c[1]+wid,c[2]-wid])
    p.append([c[0]+wid,c[1]+wid,c[2]-wid])
    p.append([c[0]+wid,c[1]-wid,c[2]-wid])
    p.append([c[0]-wid,c[1]-wid,c[2]-wid]) #same as first to close plot

    # top
    p.append([c[0]-wid,c[1]-wid,c[2]+wid])
    p.append([c[0]-wid,c[1]+wid,c[2]+wid])
    p.append([c[0]+wid,c[1]+wid,c[2]+wid])
    p.append([c[0]+wid,c[1]-wid,c[2]+wid])
    p.append([c[0]-wid,c[1]-wid,c[2]+wid]) #same as first to close plot

    # vertical sides
    p.append([c[0]-wid,c[1]-wid,c[2]+wid])
    p.append([c[0]-wid,c[1]+wid,c[2]+wid])
    p.append([c[0]-wid,c[1]+wid,c[2]-wid])
    p.append([c[0]+wid,c[1]+wid,c[2]-wid])
    p.append([c[0]+wid,c[1]+wid,c[2]+wid])
    p.append([c[0]+wid,c[1]-wid,c[2]+wid])
    p.append([c[0]+wid,c[1]-wid,c[2]-wid])

    return array(p).T


def my_calibration(sz):
    """
    Calibration function for the camera (iPhone4) used in this example.
    """
    row,col = sz
    fx = 2555*col/2592
    fy = 2586*row/1936
    K = diag([fx,fy,1])
    K[0,2] = 0.5*col
    K[1,2] = 0.5*row
    return K

img0_name = "montgomery_800_600.jpg"

img0bgr = cv2.imread(img0_name)
print("Input cv image", img0bgr.shape)
img0 = cv2.cvtColor(img0bgr, cv2.COLOR_BGR2GRAY)


cv_sift = cv2.SIFT()



kp0, desc0 = cv_sift.detectAndCompute(img0, None)


webcam = cv2.VideoCapture(0)


"""
    Tente até encontrar uma resolução suportada pela sua camera
"""
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_WIDTH, 800)
webcam.set(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT, 600)


while(True):
    ret, frame = webcam.read()

    if not ret:
        print("Failed to read from webcam. Will quit")
        sys.exit(0)

    img1bgr = frame
    img1 = cv2.cvtColor(img1bgr, cv2.COLOR_BGR2GRAY)
    kp1, desc1 = cv_sift.detectAndCompute(img1, None)


    # We use OpenCV instead of the calculus of the homography present in the book
    H = find_homography(kp0, desc0, kp1, desc1)

    # Note: always resize image to 747 x 1000 or change the K below
    # camera calibration
    K = my_calibration((747,1000))

    # 3D points at plane z=0 with sides of length 0.2
    box = cube_points([0,0,0.1],0.1)

    # project bottom square in first image
    cam1 = camera.Camera( hstack((K,dot(K,array([[0],[0],[-1]])) )) )
    # first points are the bottom square
    box_cam1 = cam1.project(homography.make_homog(box[:,:5]))


    # use H to transfer points to the second image
    box_trans = homography.normalize(dot(H,box_cam1))

    # compute second camera matrix from cam1 and H
    cam2 = camera.Camera(dot(H,cam1.P))
    A = dot(linalg.inv(K),cam2.P[:,:3])
    A = array([A[:,0],A[:,1],cross(A[:,0],A[:,1])]).T
    cam2.P[:,:3] = dot(K,A)

    # project with the second camera
    box_cam2 = cam2.project(homography.make_homog(box))





    #plot(box_cam1[0,:],box_cam1[1,:],linewidth=3)
    #title('2D projection of bottom square')
    #axis('off')

    #figure()
    #imshow(im1)
    #plot(box_trans[0,:],box_trans[1,:],linewidth=3)
    #title('2D projection transfered with H')
    #axis('off')

    # Creates a list of x-y pairs for the points to be drawn on the screen
    points2d = zip([int(x) for x in box_cam2[0,:]], [int(y) for y in box_cam2[1,:]])


    #print("points2d", points2d)
    first = points2d[0]
    for p in points2d[1:]:
        cv2.line(img1bgr, first, p, (0,0,255), 3, cv2.CV_AA)
        first = p


    cv2.imshow('OpenCV output', img1bgr)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyWindow('OpenCV output')