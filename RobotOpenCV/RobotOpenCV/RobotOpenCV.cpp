#include <opencv2/opencv.hpp>
#include <iostream>
#include <opencv2/highgui.hpp>
#include <opencv2/imgproc/imgproc.hpp>
#include <boost/asio.hpp>
#include <boost/array.hpp>
#include <boost/bind.hpp>
#include <windows.h>
#define UDP_PORT 13251
using boost::asio::ip::udp;
using boost::asio::ip::address;


int main()
{
    std::string ipSocket;
    int portSocket;

    std::cout << "what address are we connecting to?" << std::endl;
    std::cin >> ipSocket;
    std::cout << "which port are we connecting to?" << std::endl;
    std::cin >> portSocket;

    boost::asio::io_service io_service; 
    boost::asio::ip::udp::socket socket(io_service); // создание udp сокета
    boost::asio::ip::udp::endpoint server_endpoint(boost::asio::ip::address::from_string(ipSocket), portSocket); // адрес и порт, к которому прив€зан сокс


    socket.open(boost::asio::ip::udp::v4()); //прив€зка сокета к порту и адресу
    socket.bind(server_endpoint);
    boost::system::error_code err;

    auto const MASK_WINDOW = "Mask Settings";
    cv::namedWindow(MASK_WINDOW, (1920, 1080));
    


    //------------------------------------------------------------
    int minHue = 152, maxHue = 179; //значени€ оттенка
    int minSat = 47, maxSat = 205;  //значени€ насыщенности
    int minVal = 114, maxVal = 255; //значени€ €ркости
    int iLastX = -1; //координаты предыдущей позиции объекта
    int iLastY = -1;
    //-------------------------------------------------------------



    cv::createTrackbar("Min Hue", MASK_WINDOW, &minHue, 179);
    cv::createTrackbar("Max Hue", MASK_WINDOW, &maxHue, 179);
    cv::createTrackbar("Min Sat", MASK_WINDOW, &minSat, 255);
    cv::createTrackbar("Max Sat", MASK_WINDOW, &maxSat, 255);
    cv::createTrackbar("Min Val", MASK_WINDOW, &minVal, 255);
    cv::createTrackbar("Max Val", MASK_WINDOW, &maxVal, 255);


    cv::VideoCapture videoCapture(0); //инициализаци€ видеозахвата с веб-камеры

    while (true) {

        cv::Mat inputVideo;
        videoCapture.read(inputVideo);
        cv::flip(inputVideo, inputVideo, 1);
        cv::Mat inputVideoHSV;
        cv::cvtColor(inputVideo, inputVideoHSV, cv::COLOR_BGR2HSV);


        cv::Mat mask;

        cv::inRange(
            inputVideoHSV,
            cv::Scalar(minHue, minSat, minVal),
            cv::Scalar(maxHue, maxSat, maxVal),
            mask
        );
        cv::Mat resultVideo;

        cv::bitwise_and(inputVideo, inputVideo, resultVideo, mask);


        cv::imshow("Input Video", inputVideo);
        cv::imshow("Result (Masked) Video", resultVideo);



        if (cv::waitKey(30) == 27) break; //клавиша ESC дл€ выхода

        cv::Mat imgTmp; //матрица считывает кадр с видеокамеры
        videoCapture.read(imgTmp);


        cv::Mat imgLines = cv::Mat::zeros(imgTmp.size(), CV_8UC3); //матрица отслеживает движение объекта рису€ линии


        while (true)
        {
            cv::Mat imgOriginal;

            bool bSuccess = videoCapture.read(imgOriginal);



            if (!bSuccess)
            {
                std::cout << "Cannot read a frame from video stream" << std::endl;
                break;
            }

            cv::Mat imgHSV; //матрица хранит преобразованные кадры в цветовом пространстве HSV

            cvtColor(imgOriginal, imgHSV, cv::COLOR_BGR2HSV);

            cv::Mat imgThresholded; //маска определ€ет области изображени€, соответствующие заданным цветам

            inRange(imgHSV, cv::Scalar(minHue, minSat, minVal), cv::Scalar(maxHue, maxSat, maxVal), imgThresholded);


            erode(imgThresholded, imgThresholded, cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5))); //операции морфологической обработки на маске
            dilate(imgThresholded, imgThresholded, cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5)));


            dilate(imgThresholded, imgThresholded, cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5)));
            erode(imgThresholded, imgThresholded, cv::getStructuringElement(cv::MORPH_ELLIPSE, cv::Size(5, 5)));


            cv::Moments oMoments = moments(imgThresholded);

            double dM01 = oMoments.m01;
            double dM10 = oMoments.m10;
            double dArea = oMoments.m00;


            if (dArea > 10000)
            {

                int posX = dM10 / dArea;
                int posY = dM01 / dArea;

                if (iLastX >= 0 && iLastY >= 0 && posX >= 0 && posY >= 0)
                {

                    line(imgLines, cv::Point(posX, posY), cv::Point(iLastX, iLastY), cv::Scalar(0, 0, 255), 2);
                }

                iLastX = posX;
                iLastY = posY;
            }

            imshow("Thresholded Image", imgThresholded);

            imgOriginal = imgOriginal + imgLines;
            imshow("Original", imgOriginal);

           
            cv::Mat redChannel; 
            //cv::extractChannel(img, redChannel, 2); 

        }

        for (int row = 0; row < imgLines.rows; ++row) {
            uchar* pixel_ptr = imgLines.ptr<uchar>(row);
            for (int col = 0; col < imgLines.cols; ++col) {
                uchar blue = pixel_ptr[3 * col];     // —иний канал
                uchar green = pixel_ptr[3 * col + 1]; // «елЄный канал
                uchar red = pixel_ptr[3 * col + 2];   //  расный канал
               
                std::cout << "Output mat" << red << std::endl;
            }
        }

        while (true) {
            int size = 1032; // размер буффера в байтах с небольшим запасом
            char data[1024];
            boost::asio::ip::udp::endpoint client_endpoint;
            boost::system::error_code error;

            // отправл€ет данные
            size_t message = socket.send(boost::asio::buffer(data, size));

            if (!error) {
                std::cout << "Sent data to " << client_endpoint.address().to_string() << ":" << client_endpoint.port() << std::endl;
                std::cout.write(data, message);
                std::cout << std::endl;
            }
            else {
                std::cerr << "Error sending data: " << error.message() << std::endl;
            }
        }

        return 0;
    }
}

