/***************************************************************************
 *
 * Authors:    Carlos Oscar            coss@cnb.uam.es (1999)
 *
 * Unidad de  Bioinformatica of Centro Nacional de Biotecnologia , CSIC
 *
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or   
 * (at your option) any later version.                                 
 *                                                                     
 * This program is distributed in the hope that it will be useful,     
 * but WITHOUT ANY WARRANTY; without even the implied warranty of      
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the       
 * GNU General Public License for more details.                        
 *                                                                     
 * You should have received a copy of the GNU General Public License   
 * along with this program; if not, write to the Free Software         
 * Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA            
 * 02111-1307  USA                                                     
 *                                                                     
 *  All comments concerning this program package may be sent to the    
 *  e-mail address 'xmipp@cnb.uam.es'                                  
 ***************************************************************************/

/* INCLUDES ---------------------------------------------------------------- */
#include <XmippData/xmippArgs.hh>
#include <XmippData/xmippSelFiles.hh>
#include <XmippData/xmippGeometry.hh>
#include <XmippData/xmippHistograms.hh>
#include <XmippInterface/xmippSpider.hh>
#include <fstream.h>

/* PROTOTYPES -------------------------------------------------------------- */
void Usage();

/* MAIN -------------------------------------------------------------------- */
int main (int argc,char *argv[]) {
   string          ang1="rot",ang2="tilt",ang3="psi";
   DocFile         angles;
   FileName        fn_ang, fn_sel, fn_hist, fn_ps;
   int             steps;
   int             tell;
   float           R, r;
   float           rot_view;
   float           tilt_view;
   int             up_down_correction;

// Check the command line ==================================================
   try {
      fn_sel=get_param(argc,argv,"-sel","");
      fn_ang=get_param(argc,argv,"-ang","");
      fn_hist=get_param(argc,argv,"-hist","");
      fn_ps=get_param(argc,argv,"-ps","");
      steps=AtoI(get_param(argc,argv,"-steps","100"));
      tell=check_param(argc,argv,"-show_process");
      R=AtoF(get_param(argc,argv,"-R","60"));
      r=AtoF(get_param(argc,argv,"-r","1.5"));
      rot_view =AtoF(get_param(argc,argv,"-rot_view",  "0"));
      tilt_view=AtoF(get_param(argc,argv,"-tilt_view","30"));
      up_down_correction=check_param(argc,argv,"-up_down_correction");

      // Angle order
      int i;
      if ((i=position_param(argc,argv,"-order"))!=-1) {
         if (i+3>=argc) {
            cout << "Angular distribution: Not enough parameters behind -ang\n";
            Usage();
            exit(1);
         }
         ang1=argv[i+1];
         ang2=argv[i+2];
         ang3=argv[i+3];
      }

   // Check they are "rot", "tilt", and "psi"
   check_angle_descr(ang1);
   check_angle_descr(ang2);
   check_angle_descr(ang3);
   if (ang1[1]==ang2[1] || ang1[1]==ang3[1] || ang2[1]==ang3[1])
      REPORT_ERROR(1,"Angular distribution: There is an angle twice in the angle order");

   // Check there is some input
   if (fn_ang=="" && fn_sel=="")
      REPORT_ERROR(1,"Angular distribution: There is no input information");
   } catch (Xmipp_error XE) {cout << XE; Usage(); exit(1);}

   try {
// Get angles ==============================================================
   if (fn_ang!="")
      angles.read(fn_ang);
   else {
      SelFile selfile(fn_sel);
      extract_angles(selfile, angles, ang1, ang2, ang3);
   }
   int AngleNo=angles.dataLineNo();
   if (AngleNo==0)
      EXIT_ERROR(1,"Angular distribution: Input files doesn't contain angular information");

// Build vector table ======================================================
   #define GET_ANGLES(i) \
       angles.get_angles(i,rot,tilt,psi,ang1,ang2,ang3); \
       if (up_down_correction && ABS(tilt)>90) \
          Euler_up_down(rot,tilt,psi,rot,tilt,psi);

   double rot, tilt, psi;
   vector< matrix1D<double> > v;
   v.reserve(AngleNo);
   for (int i=0; i<AngleNo; i++) {
       matrix1D<double> aux(3);
       GET_ANGLES(i+1);
       Euler_direction(rot, tilt, psi, aux);
       v.push_back(aux);
   }

// Compute histogram of distances =============================================
   if (fn_hist!="") {
      matrix1D<double> dist;
      #define di VEC_ELEM(dist,i)
      #define dj VEC_ELEM(dist,j)

      #define SHOW {\
         GET_ANGLES(i+1); \
         cout << i << " " << rot << " " << tilt << " v[i]=" \
             << v[i].transpose() << endl; \
         GET_ANGLES(j+1); \
         cout << j << " " << rot << " " << tilt << " v[j]=" \
             << v[j].transpose() << endl; \
         cout << " d= " << d << endl << endl; \
      }

      // Compute minimum distance table
      dist.init_zeros(AngleNo);
      for (int i=0; i<AngleNo; i++)
          for (int j=i+1; j<AngleNo; j++) {
              double d=spherical_distance(v[i],v[j]);
              if (di==0 || d<di) {di=d; if (tell) SHOW;}
              if (dj==0 || d<dj) {dj=d; if (tell) SHOW;}
          }

      histogram1D dist_hist;
      double min, max; dist.compute_double_minmax(min,max);
      dist_hist.init(min,max,steps);
      for (int i=0; i<AngleNo; i++) dist_hist.insert_value(di);
      dist_hist.write(fn_hist);
   }
   
// Show distribution as triangles ==========================================
   if (fn_ps!="") {
      ofstream fh_ps;
      fh_ps.open(fn_ps.c_str(),ios::out);
      if (!fh_ps)
         EXIT_ERROR(1,(string)"Ang_distribution: Cannot open "+fn_ps+" for output");

      fh_ps << "%%!PS-Adobe-2.0\n";
      fh_ps << "%% Creator: Angular Distribution\n";
      fh_ps << "%% Title: Angular distribution of " << fn_sel << "\n";
      fh_ps << "%% Pages: 1\n";

      #define TO_PS(x,y) \
         tmp=y; \
         y=400.0f-x*250.0f/60; \
         x=300.0f+tmp*250.0f/60;

      matrix1D<double> p1(4),p2(4),p3(4);
      matrix2D<double> A,euler_view;
      Euler_angles2matrix(rot_view,tilt_view,0.0f,euler_view);
      double tmp;
      for (int i=0; i<AngleNo; i++) {
          // Initially the triangle is on the floor of the projection plane
          VECTOR_R3(p1,    0   , r*2/3*SIND(60),0);
          VECTOR_R3(p2, r/2*0.6,-r*1/3*SIND(60),0);
          VECTOR_R3(p3,-r/2*0.6,-r*1/3*SIND(60),0);

          // Convert to homogeneous coordinates
          p1(3)=1; p2(3)=1; p3(3)=1;

          // Compute Transformation matrix
          GET_ANGLES(i+1);
          Euler_angles2matrix(rot,tilt,psi,A);

          // We go from the projeciton plane to the universal coordinates
          A=A.transpose();

          // Convert to homogeneous coordinates and apply a translation
          // to the sphere of radius R
          A.resize(4,4);
          A(0,3)=R*XX(v[i]); A(1,3)=R*YY(v[i]); A(2,3)=R*ZZ(v[i]); A(3,3)=1;

          // Convert triangle coordinates to universal ones
          p1=A*p1;
          p2=A*p2;
          p3=A*p3;

          // Project this triangle onto the view plane and write in PS
          matrix1D<double> pp(3);
          Uproject_to_plane(p1,euler_view,pp);
          TO_PS(XX(pp),YY(pp));
          fh_ps << "newpath\n";
          fh_ps << XX(pp) << " " << YY(pp) << " moveto\n";
          
          Uproject_to_plane(p2,euler_view,pp);
          TO_PS(XX(pp),YY(pp));
          fh_ps << XX(pp) << " " << YY(pp) << " lineto\n";

          Uproject_to_plane(p3,euler_view,pp);
          TO_PS(XX(pp),YY(pp));
          fh_ps << XX(pp) << " " << YY(pp) << " lineto\n";

          Uproject_to_plane(p1,euler_view,pp);
          TO_PS(XX(pp),YY(pp));
          fh_ps << XX(pp) << " " << YY(pp) << " lineto\n";

          fh_ps << "closepath\nstroke\n";
      }
      fh_ps << "showpage\n";
      fh_ps.close();
   }

   } catch (Xmipp_error XE) {cout << XE;}

}

/* Usage ------------------------------------------------------------------- */
void Usage() {
    cout << "Usage:\n";
    cout << "   ang_distribution <options>\n";
    cout << "   Where <options> are:\n";
    cout << "      (-sel <sel_file> |            : selection file with the set of images\n"
         << "       -ang <ang_file>              : Spider document file with the angles\n"
         << "      [-order <ang1> <ang2> <ang3>]): where ang1, ang2 and ang3 are\n"
         << "                                      either psi, psi, tilt, tilt,\n"
         << "                                      rot or rot. The default\n"
         << "                                      order is rot, tilt and psi.\n"
         << "      [-hist <doc_file>]            : histogram of distances\n"
         << "      [-steps <stepno=100>]         : number of divisions in the histogram\n"
         << "      [-show_process]               : show distances.\n"
         << "      [-ps <PS file out>]           : PS file with the topological sphere\n"
         << "      [-R <big_sphere_radius=60>]   : for the PS file\n"
         << "      [-r <triangle side=1.5>]      : for the PS file\n"
         << "      [-rot_view <rot angle=0>]     : rotational angle for the view\n"
         << "      [-tilt_view <tilt angle=30>]  : tilting angle for the view\n"
         << "      [-up_down_correction]         : correct angles so that a semisphere\n"
         << "                                      is shown\n";
}

/* ------------------------------------------------------------------------- */
/* Menus                                                                     */
/* ------------------------------------------------------------------------- */
/*Colimate:
   PROGRAM Ang_distribution {
      url="http://www.cnb.uam.es/~bioinfo/NewXmipp/Applications/Src/Ang_distribution/Help/ang_distribution.html";
      help="Show angular distribution";
      OPEN MENU Ang_distribution;
      COMMAND LINES {
         + Angle_Set:
             ang_distribution -ang $ANGFILE
                [-ang $ANG1 $ANG2 $ANG3] [$ANGL1 $ANGL2 $ANGL3]
                [-hist $HISTFILE [-steps $STEPNO] [-show_process]]
                [-ps $PSFILE [-R $RADIUS] [-r $SIDE] [-rot_view $ROT]
                   [-tilt_view $TILT] [-up_down_correction]]
         + SelFile:
             ang_distribution -sel $SELFILE OPT(-hist) OPT(-ps)
      }
      PARAMETER DEFINITIONS {
         $ANGFILE {
            label="DocFile with angles";
            type=FILE EXISTING;
         }
         $SELFILE {
            label="Selection file";
            type=FILE EXISTING;
         }
         #include "angles.mnu"
         OPT(-hist) {label="Generate Distance Histogram";}
            $HISTFILE {
               label="Output histogram file";
               type=FILE;
            }
            $STEPNO {
               label="Histogram steps";
               help="The histogram is divided in this number of steps";
               type=NATURAL;
               by default=100;
            }
            OPT(-show_process) {label="Show process information";}
         OPT(-ps) {label="Generate Topological sphere";}
            $PSFILE {
               label="OutputPostscript file";
               type=FILE;
            }
            $RADIUS {
               label="Topological sphere radius";
               type=FLOAT [0...];
               by default=60;
            }
            $SIDE {
               label="Triangle side length";
               type=FLOAT [0...];
               by default=1.5;
            }
            $ROT {
               label="Rotational angle for Point of view";
               help="degrees";
               type=FLOAT [0...360];
               by default=0;
            }
            $TILT {
               label="Tilting angle for Point of view";
               help="degrees";
               type=FLOAT [0...360];
               by default=30;
            }
            OPT(-up_down_correction) {label= "Up-Down correction";}
      }
   }
   
   MENU Ang_distribution {
      "I/O Parameters"
      $ANGFILE
      OPT($ANGL1)
      $SELFILE
      "Distance Histogram Parameters"
      OPT(-hist)
      "Topological Sphere Parameters"
      OPT(-ps)
   }
*/
